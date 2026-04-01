from keyboard import add_hotkey, remove_hotkey

from .clicker import ClickerController
from .log_monitor import LogMonitor
from .osc_client import VRChatOSCClient
from .settings import MAX_CLICK_DELAY_MS, MIN_CLICK_DELAY_MS, SettingsStore
from .single_instance import SingleInstanceManager
from .tray import TrayController
from .ui import MainWindow


class DekapuOscClickerApp:
    def __init__(self):
        self.settings = SettingsStore()
        self.osc_client = VRChatOSCClient()
        self.ui = None
        self.hotkey_f1 = None
        self.hotkey_f2 = None

        self.clicker = ClickerController(self.osc_client)
        self.log_monitor = LogMonitor(self._send_chatbox_message)
        self.tray = None
        self.single_instance = SingleInstanceManager(self._wake_existing_window)

    def attach_ui(self, ui):
        self.ui = ui
        self.tray = TrayController(ui)
        self.clicker.status_callback = self.ui.set_status
        self.log_monitor.status_callback = self.ui.schedule_status

    def get_saved_log_dir(self):
        return self.settings.get_log_dir()

    def save_log_dir(self, log_dir):
        self.settings.set_log_dir(log_dir)

    def get_saved_click_delay_ms(self):
        return self.settings.get_click_delay_ms()

    def save_click_delay_ms(self, click_delay_ms):
        self.settings.set_click_delay_ms(click_delay_ms)

    def get_saved_languages(self):
        return self.settings.get_languages()

    def save_languages(self, languages):
        self.settings.set_languages(languages)

    @staticmethod
    def get_click_delay_limits_ms():
        return MIN_CLICK_DELAY_MS, MAX_CLICK_DELAY_MS

    def apply_click_delay(self, raw_value):
        delay_seconds = self.clicker.apply_delay(raw_value)
        delay_ms = int(round(delay_seconds * 1000))
        if delay_ms < MIN_CLICK_DELAY_MS or delay_ms > MAX_CLICK_DELAY_MS:
            raise ValueError(f"点击频率必须在 {MIN_CLICK_DELAY_MS}-{MAX_CLICK_DELAY_MS} ms 之间")
        return delay_ms

    def start_clicking(self, raw_value):
        delay_ms = self.apply_click_delay(raw_value)
        self.clicker.start(str(delay_ms))

    def stop_clicking(self):
        self.clicker.stop()

    def _send_chatbox_message(self, text):
        try:
            self.osc_client.send_chatbox_message(text)
        except Exception as exc:
            raise ValueError(f"发送聊天框消息失败：{exc}") from exc

    def start_monitoring(self, log_dir, selected_languages):
        return self.log_monitor.start(lambda: log_dir, selected_languages)

    def stop_monitoring(self):
        self.log_monitor.stop()

    def ensure_tray_started(self):
        if self.tray is None:
            return False
        started = self.tray.ensure_started()
        if not started and self.ui is not None:
            self.ui.set_status("状态：当前环境不支持系统托盘，关闭窗口将直接退出")
        return started

    def register_hotkeys(self):
        self.hotkey_f1 = add_hotkey("F1", lambda: self.start_clicking(self.ui.delay_var.get()))
        self.hotkey_f2 = add_hotkey("F2", self.stop_clicking)

    def remove_hotkeys(self):
        if self.hotkey_f1 is not None:
            try:
                remove_hotkey(self.hotkey_f1)
            except Exception:
                pass
            self.hotkey_f1 = None

        if self.hotkey_f2 is not None:
            try:
                remove_hotkey(self.hotkey_f2)
            except Exception:
                pass
            self.hotkey_f2 = None

    def _wake_existing_window(self):
        if self.ui is None:
            return
        self.ui.schedule_show_from_external_request()

    def start_single_instance_guard(self):
        return self.single_instance.start()

    def notify_existing_instance(self):
        return self.single_instance.notify_existing_instance()

    def close_app(self):
        self.stop_clicking()
        self.stop_monitoring()
        self.remove_hotkeys()
        self.single_instance.stop()
        if self.tray is not None:
            self.tray.stop()
        if self.ui is not None:
            self.ui.root.quit()
            self.ui.root.destroy()


def main():
    app = DekapuOscClickerApp()
    if not app.start_single_instance_guard():
        app.notify_existing_instance()
        return

    ui = MainWindow(app)
    app.attach_ui(ui)
    app.register_hotkeys()
    ui.run()
