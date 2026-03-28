from pathlib import Path
from threading import Event, Thread

from .constants import LOG_FILE_PATTERN, MONITOR_POLL_INTERVAL
from .dsm_parser import extract_generated_url_from_line, extract_last_generated_url, extract_sp_from_generated_url


class LogMonitor:
    def __init__(self, send_chatbox_message, status_callback=None):
        self.send_chatbox_message = send_chatbox_message
        self.status_callback = status_callback or (lambda _text: None)
        self.monitor_stop_event = Event()
        self.monitor_worker = None
        self.monitor_current_file = None
        self.monitor_current_offset = 0
        self.waiting_for_generated_url = False
        self.selected_languages = ["zh", "en", "ja"]
        self.language_index = 0

    def _set_status(self, text):
        self.status_callback(text)

    @staticmethod
    def _debug_log(message):
        print(f"[log_monitor] {message}")

    @staticmethod
    def _format_scaled_value(value, divisor, suffix):
        scaled = value / divisor
        text = f"{scaled:.1f}".rstrip("0").rstrip(".")
        return f"{text}{suffix}"

    def _format_number(self, sp_value, language):
        try:
            value = int(sp_value)
        except ValueError:
            return str(sp_value)

        if language == "en":
            if value >= 1_000_000_000_000:
                return self._format_scaled_value(value, 1_000_000_000_000, "T")
            if value >= 1_000_000_000:
                return self._format_scaled_value(value, 1_000_000_000, "B")
            if value >= 1_000_000:
                return self._format_scaled_value(value, 1_000_000, "M")
            if value >= 1_000:
                return self._format_scaled_value(value, 1_000, "K")
            return str(value)

        if language == "ja":
            if value >= 1_000_000_000_000:
                return self._format_scaled_value(value, 1_000_000_000_000, "兆")
            if value >= 100_000_000:
                return self._format_scaled_value(value, 100_000_000, "億")
            if value >= 10_000:
                return self._format_scaled_value(value, 10_000, "万")
            return str(value)

        if value >= 1_000_000_000_000:
            return self._format_scaled_value(value, 1_000_000_000_000, "万亿")
        if value >= 100_000_000:
            return self._format_scaled_value(value, 100_000_000, "亿")
        if value >= 10_000:
            return self._format_scaled_value(value, 10_000, "万")
        return str(value)

    def _build_sp_message(self, sp_value, advance=False):
        if not self.selected_languages:
            raise ValueError("请至少选择一种发送语言")

        language = self.selected_languages[self.language_index]
        formatted_value = self._format_number(sp_value, language)

        if language == "en":
            message = f"Current SP: {formatted_value}"
        elif language == "ja":
            message = f"現在のSP: {formatted_value}"
        else:
            message = f"当前sp:{formatted_value}"

        if advance:
            self.language_index = (self.language_index + 1) % len(self.selected_languages)

        return message

    @staticmethod
    def get_latest_vrchat_log_file(log_dir):
        log_path = Path(log_dir)
        if not log_dir:
            raise ValueError("请先选择 VRChat 日志目录")
        if not log_path.exists():
            raise ValueError("日志目录不存在")
        if not log_path.is_dir():
            raise ValueError("日志目录不是文件夹")

        log_files = list(log_path.glob(LOG_FILE_PATTERN))
        if not log_files:
            raise ValueError("未找到 output_log_*.txt 日志文件")

        return max(log_files, key=lambda path: path.stat().st_mtime)

    def get_current_sp_message(self, log_dir):
        latest_log = self.get_latest_vrchat_log_file(log_dir)
        generated_url = extract_last_generated_url(latest_log)
        sp_value = extract_sp_from_generated_url(generated_url)
        return self._build_sp_message(sp_value, advance=False), sp_value

    def initialize(self, log_dir):
        latest_log = self.get_latest_vrchat_log_file(log_dir)
        self.monitor_current_file = latest_log
        try:
            self.monitor_current_offset = latest_log.stat().st_size
        except OSError as exc:
            raise ValueError(f"读取日志状态失败：{exc}") from exc
        self._debug_log(f"start monitoring file={latest_log} offset={self.monitor_current_offset}")
        return latest_log

    def process_new_log_lines(self, log_file):
        try:
            with log_file.open("r", encoding="utf-8", errors="replace") as handle:
                handle.seek(self.monitor_current_offset)
                new_content = handle.read()
                self.monitor_current_offset = handle.tell()
        except OSError as exc:
            raise ValueError(f"读取日志失败：{exc}") from exc

        if not new_content:
            return

        self._debug_log(f"read {len(new_content)} chars from {log_file.name}, new_offset={self.monitor_current_offset}")

        for line in new_content.splitlines():
            stripped_line = line.strip()

            if self.waiting_for_generated_url:
                if not stripped_line:
                    continue
                self._debug_log(f"using next line as DSM url: {stripped_line}")
                self.waiting_for_generated_url = False
                try:
                    sp_value = extract_sp_from_generated_url(stripped_line)
                    message = self._build_sp_message(sp_value, advance=False)
                    self._debug_log(f"parsed sp={sp_value}, sending chatbox message: {message}")
                    self.send_chatbox_message(message)
                    self._build_sp_message(sp_value, advance=True)
                    self._set_status(f"状态：监听中，已发送 sp={sp_value}")
                except ValueError as exc:
                    self._debug_log(f"failed to parse/send DSM continuation line: {exc}")
                    self._set_status(f"状态：监听中，跳过异常日志：{exc}")
                continue

            generated_url = extract_generated_url_from_line(line)
            if generated_url:
                self._debug_log(f"matched inline DSM line: {line}")
                try:
                    sp_value = extract_sp_from_generated_url(generated_url)
                    message = self._build_sp_message(sp_value, advance=False)
                    self._debug_log(f"parsed sp={sp_value}, sending chatbox message: {message}")
                    self.send_chatbox_message(message)
                    self._build_sp_message(sp_value, advance=True)
                    self._set_status(f"状态：监听中，已发送 sp={sp_value}")
                except ValueError as exc:
                    self._debug_log(f"failed to parse/send inline DSM line: {exc}")
                    self._set_status(f"状态：监听中，跳过异常日志：{exc}")
                continue

            if "[DSM SaveURL] Generated URL:" in line:
                self.waiting_for_generated_url = True
                self._debug_log("matched DSM marker line, waiting for URL on next line")

    def _monitor_log_loop(self, get_log_dir):
        while not self.monitor_stop_event.is_set():
            try:
                current_log_dir = get_log_dir()
                latest_log = self.get_latest_vrchat_log_file(current_log_dir)
                if latest_log != self.monitor_current_file:
                    self.monitor_current_file = latest_log
                    self.monitor_current_offset = latest_log.stat().st_size
                    self._debug_log(f"switched to new file={latest_log} offset={self.monitor_current_offset}")
                    self._set_status(f"状态：监听中，已切换到 {latest_log.name}")
                self.process_new_log_lines(self.monitor_current_file)
            except ValueError as exc:
                self._debug_log(f"monitor error: {exc}")
                self._set_status(f"状态：监听异常：{exc}")

            if self.monitor_stop_event.wait(MONITOR_POLL_INTERVAL):
                break

    def start(self, get_log_dir, selected_languages):
        if not selected_languages:
            raise ValueError("请至少选择一种发送语言")

        if self.monitor_worker is not None and self.monitor_worker.is_alive():
            self._debug_log("start requested but monitor already running")
            return self.monitor_current_file

        self.selected_languages = selected_languages
        self.language_index = 0
        latest_log = self.initialize(get_log_dir())
        self.monitor_stop_event.clear()
        self.monitor_worker = Thread(target=self._monitor_log_loop, args=(get_log_dir,), daemon=True)
        self.monitor_worker.start()
        self._debug_log(f"monitor thread started for {latest_log}, languages={selected_languages}")
        self._set_status(f"状态：监听中，当前文件 {latest_log.name}")
        return latest_log

    def stop(self):
        self.monitor_stop_event.set()
        self._debug_log("monitor stopped")
        self.monitor_worker = None
        self.monitor_current_file = None
        self.monitor_current_offset = 0
        self.waiting_for_generated_url = False
        self.language_index = 0
        self._set_status("状态：已停止监听")
