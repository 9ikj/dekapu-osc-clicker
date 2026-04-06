from threading import Event, Lock, Thread
from time import monotonic, sleep

from .constants import DEFAULT_CLICK_DELAY_MS, DEFAULT_CLICK_PRESS_DURATION


class ClickerController:
    def __init__(self, osc_client, status_callback=None):
        self.osc_client = osc_client
        self.status_callback = status_callback or (lambda _text: None)
        self.stop_event = Event()
        self.state_lock = Lock()
        self.worker = None
        self.running = False
        self.click_delay = DEFAULT_CLICK_DELAY_MS / 1000.0
        self.press_duration = DEFAULT_CLICK_PRESS_DURATION

    def _set_status(self, text):
        self.status_callback(text)

    def _running_status_text(self):
        return f"状态：运行中，间隔 {self.click_delay * 1000:.0f} ms，按下 {self.press_duration * 1000:.0f} ms"

    def _click_loop(self):
        next_click_time = monotonic()
        while not self.stop_event.is_set():
            with self.state_lock:
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
                with self.state_lock:
                    self.stop_event.set()
                    self.running = False
                    self.worker = None
                self._set_status(f"状态：发送点击失败：{exc}")
                return

            next_click_time = max(next_click_time + interval, monotonic())

        with self.state_lock:
            self.running = False
            self.worker = None

    @staticmethod
    def validate_delay(raw_value):
        try:
            value = float(raw_value)
        except (TypeError, ValueError) as exc:
            raise ValueError("点击频率必须是数字") from exc

        if value <= 0:
            raise ValueError("点击频率必须大于 0 ms")

        return value / 1000.0

    def apply_delay(self, raw_value):
        delay = self.validate_delay(raw_value)
        with self.state_lock:
            self.click_delay = delay
            running = self.running
        if running:
            self._set_status(self._running_status_text())
        return delay

    def start(self, raw_value):
        delay = self.validate_delay(raw_value)
        with self.state_lock:
            if self.running:
                return False
            self.click_delay = delay
            self.stop_event.clear()
            self.running = True
            self.worker = Thread(target=self._click_loop, daemon=True)
            self.worker.start()
        self._set_status(self._running_status_text())
        return True

    def stop(self):
        with self.state_lock:
            worker = self.worker
            was_running = self.running
            self.stop_event.set()
            self.running = False

        if worker is not None and worker.is_alive():
            worker.join(timeout=self.press_duration + 0.5)

        with self.state_lock:
            if self.worker is worker:
                self.worker = None

        if was_running:
            self._set_status("状态：已停止")
        else:
            self._set_status("状态：已停止")
