try:
    from keyboard import add_hotkey, remove_hotkey
except Exception:  # pragma: no cover - optional runtime dependency
    add_hotkey = None
    remove_hotkey = None

from .clicker import ClickerController
from .constants import BASE_APP_TITLE, STATS_WEB_PORT, get_stats_db_file
from .log_monitor import LogMonitor
from .osc_client import VRChatOSCClient
from .settings import MAX_CLICK_DELAY_MS, MIN_CLICK_DELAY_MS, SettingsStore
from .single_instance import SingleInstanceManager
from .stats_store import StatsStore
from .stats_web import StatsWebServer
from .tray import TrayController
from .ui import MainWindow


class DekapuOscClickerApp:
    def __init__(self):
        self.settings = SettingsStore()
        self.stats_store = StatsStore(get_stats_db_file())
        self.stats_web = StatsWebServer(self.stats_store, get_bind_host=self.get_stats_web_bind_host)
        self.osc_client = VRChatOSCClient()
        self.ui = None
        self.hotkey_f1 = None
        self.hotkey_f2 = None

        self.clicker = ClickerController(self.osc_client)
        self.log_monitor = LogMonitor(self._send_chatbox_message, stats_store=self.stats_store)
        self.tray = None
        self.single_instance = SingleInstanceManager(BASE_APP_TITLE)

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
        self.log_monitor.update_selected_languages(languages)

    def get_send_enabled(self):
        return self.settings.get_send_enabled()

    def save_send_enabled(self, send_enabled):
        self.settings.set_send_enabled(send_enabled)

    def get_stats_web_allow_lan(self):
        return self.settings.get_stats_web_allow_lan()

    def save_stats_web_allow_lan(self, allow_lan):
        self.settings.set_stats_web_allow_lan(allow_lan)

    def set_stats_web_allow_lan(self, allow_lan):
        self.save_stats_web_allow_lan(allow_lan)
        self.restart_stats_web()
        host = self.get_stats_web_bind_host()
        return host, STATS_WEB_PORT

    def get_stats_web_bind_host(self):
        return "0.0.0.0" if self.get_stats_web_allow_lan() else "127.0.0.1"

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
        if not self.get_send_enabled():
            return False
        try:
            self.osc_client.send_chatbox_message(text)
        except Exception as exc:
            raise ValueError(f"发送聊天框消息失败：{exc}") from exc
        return True

    def start_monitoring(self, selected_languages):
        return self.log_monitor.start(self.get_saved_log_dir, selected_languages)

    def try_start_saved_monitoring(self):
        selected_languages = self.get_saved_languages()
        try:
            self.start_monitoring(selected_languages)
        except ValueError as exc:
            return False, str(exc)
        return True, None

    def is_monitoring(self):
        worker = self.log_monitor.monitor_worker
        return worker is not None and worker.is_alive()

    def restart_monitoring(self):
        """停止当前监控（如果有）并尝试用当前保存的日志目录重新启动。"""
        self.stop_monitoring()
        selected_languages = self.get_saved_languages()
        try:
            self.start_monitoring(selected_languages)
            return True, None
        except ValueError as exc:
            return False, str(exc)

    def stop_monitoring(self):
        self.log_monitor.stop()

    def start_stats_web(self):
        try:
            self.stats_web.ensure_started()
        except Exception as exc:
            if self.ui is not None:
                self.ui.set_status(f"状态：统计页面服务启动失败（端口 {STATS_WEB_PORT}）：{exc}")
            return False
        return True

    def restart_stats_web(self):
        was_running = self.stats_web.server is not None
        self.stats_web.stop()
        if was_running:
            self.stats_web.ensure_started()
        return was_running

    def open_stats_page(self):
        return self.stats_web.open_page("/")

    def open_stats_changes_page(self):
        return self.stats_web.open_page("/changes")

    def ensure_tray_started(self):
        if self.tray is None:
            return False
        started = self.tray.ensure_started()
        if not started and self.ui is not None:
            self.ui.set_status("状态：当前环境不支持系统托盘，关闭窗口将直接退出")
        return started

    def register_hotkeys(self):
        if add_hotkey is None or remove_hotkey is None:
            if self.ui is not None:
                self.ui.set_status("状态：当前环境缺少 keyboard 依赖，全局热键不可用，但界面仍可正常使用")
            return False
        try:
            self.hotkey_f1 = add_hotkey("F1", lambda: self.start_clicking(self.ui.delay_var.get()))
            self.hotkey_f2 = add_hotkey("F2", self.stop_clicking)
        except Exception as exc:
            self.remove_hotkeys()
            if self.ui is not None:
                self.ui.set_status(f"状态：全局热键注册失败，但界面仍可正常使用：{exc}")
            return False
        return True

    def remove_hotkeys(self):
        if self.hotkey_f1 is not None and remove_hotkey is not None:
            try:
                remove_hotkey(self.hotkey_f1)
            except Exception:
                pass
        self.hotkey_f1 = None

        if self.hotkey_f2 is not None and remove_hotkey is not None:
            try:
                remove_hotkey(self.hotkey_f2)
            except Exception:
                pass
        self.hotkey_f2 = None

    def start_single_instance_guard(self):
        return self.single_instance.start()

    def get_single_instance_warning(self):
        return self.single_instance.last_error

    def notify_existing_instance(self):
        return self.single_instance.notify_existing_instance()

    def close_app(self):
        self.stop_clicking()
        self.stop_monitoring()
        self.remove_hotkeys()
        self.single_instance.stop()
        self.stats_web.stop()
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
    warning = app.get_single_instance_warning()
    if warning:
        ui.set_status(f"状态：{warning}")
    app.start_stats_web()
    app.register_hotkeys()
    ui.apply_startup_monitoring_state(*app.try_start_saved_monitoring())
    ui.run()
