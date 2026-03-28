from keyboard import add_hotkey, remove_hotkey

from .clicker import ClickerController
from .log_monitor import LogMonitor
from .osc_client import VRChatOSCClient
from .settings import SettingsStore
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

    def attach_ui(self, ui):
        self.ui = ui
        self.clicker.status_callback = self.ui.set_status
        self.log_monitor.status_callback = self.ui.schedule_status

    def get_saved_log_dir(self):
        return self.settings.get_log_dir()

    def save_log_dir(self, log_dir):
        self.settings.set_log_dir(log_dir)

    def apply_click_delay(self, raw_value):
        return self.clicker.apply_delay(raw_value)

    def start_clicking(self, raw_value):
        self.clicker.start(raw_value)

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

    def close_app(self):
        self.stop_clicking()
        self.stop_monitoring()
        self.remove_hotkeys()
        if self.ui is not None:
            self.ui.root.destroy()


def main():
    app = DekapuOscClickerApp()
    ui = MainWindow(app)
    app.attach_ui(ui)
    app.register_hotkeys()
    ui.run()
