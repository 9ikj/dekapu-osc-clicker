from threading import Event, Thread
from time import monotonic, sleep

from .constants import DEFAULT_CLICK_DELAY, DEFAULT_CLICK_PRESS_DURATION


class ClickerController:
    def __init__(self, osc_client, status_callback=None):
        self.osc_client = osc_client
        self.status_callback = status_callback or (lambda _text: None)
        self.stop_event = Event()
        self.worker = None
        self.running = False
        self.click_delay = DEFAULT_CLICK_DELAY
        self.press_duration = DEFAULT_CLICK_PRESS_DURATION

    def _set_status(self, text):
        self.status_callback(text)

    def _running_status_text(self):
        return f"状态：运行中，间隔 {self.click_delay:.3f} 秒，按下 {self.press_duration:.3f} 秒"

    def _click_loop(self):
        next_click_time = monotonic()
        while not self.stop_event.is_set():
            interval = self.click_delay
            now = monotonic()
            wait_time = next_click_time - now
            if wait_time > 0 and self.stop_event.wait(wait_time):
                break

            try:
                self.osc_client.press_use_right()
                sleep(self.press_duration)
                self.osc_client.release_use_right()
            except Exception as exc:
                self.stop_event.set()
                self.running = False
                self._set_status(f"状态：发送点击失败：{exc}")
                break

            next_click_time = max(next_click_time + interval, monotonic())

    @staticmethod
    def validate_delay(raw_value):
        try:
            value = float(raw_value)
        except ValueError as exc:
            raise ValueError("延迟必须是数字") from exc

        if value <= 0:
            raise ValueError("延迟必须大于 0")

        return value

    def apply_delay(self, raw_value):
        self.click_delay = self.validate_delay(raw_value)
        if self.running:
            self._set_status(self._running_status_text())
        return self.click_delay

    def start(self, raw_value):
        if self.running:
            return

        self.click_delay = self.validate_delay(raw_value)
        self.stop_event.clear()
        self.worker = Thread(target=self._click_loop, daemon=True)
        self.worker.start()
        self.running = True
        self._set_status(self._running_status_text())

    def stop(self):
        if not self.running:
            self._set_status("状态：已停止")
            return

        self.stop_event.set()
        self.running = False
        self._set_status("状态：已停止")
