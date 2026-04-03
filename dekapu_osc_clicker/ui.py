import tkinter as tk
from tkinter import filedialog, messagebox

from .constants import APP_TITLE, DEFAULT_CLICK_DELAY_MS, WINDOW_SIZE, get_assets_dir
from .icon_data import WINDOW_ICON_PNG_BASE64


class MainWindow:
    def __init__(self, app_controller):
        self.app = app_controller
        self.root = tk.Tk()
        self.root.title(APP_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.resizable(False, False)
        self._is_hidden_to_tray = False

        self._apply_window_icon()

        self.delay_var = tk.StringVar(value=str(self.app.get_saved_click_delay_ms() or DEFAULT_CLICK_DELAY_MS))
        self.log_dir_var = tk.StringVar(value=self.app.get_saved_log_dir())
        self.monitor_var = tk.BooleanVar(value=False)

        saved_languages = set(self.app.get_saved_languages())
        self.language_zh_var = tk.BooleanVar(value="zh" in saved_languages)
        self.language_en_var = tk.BooleanVar(value="en" in saved_languages)
        self.language_ja_var = tk.BooleanVar(value="ja" in saved_languages)
        self.status_var = tk.StringVar(value="状态：已停止")

        self._build_ui()
        self.delay_var.trace_add("write", self._apply_click_delay)
        self.root.protocol("WM_DELETE_WINDOW", self._handle_window_close)
        self.root.bind("<Unmap>", self._on_root_unmap)
        self.root.bind("<Map>", self._on_root_map)

    def _apply_window_icon(self):
        assets_dir = get_assets_dir()
        ico_path = assets_dir / "sp_assistant_icon.ico"
        png_path = assets_dir / "sp_assistant_icon.png"

        if ico_path.exists():
            try:
                self.root.iconbitmap(default=str(ico_path))
            except Exception:
                pass

        try:
            self._window_icon = tk.PhotoImage(data=WINDOW_ICON_PNG_BASE64)
            self.root.iconphoto(True, self._window_icon)
            return
        except Exception:
            pass

        if png_path.exists():
            try:
                self._window_icon = tk.PhotoImage(file=str(png_path))
                self.root.iconphoto(True, self._window_icon)
            except Exception:
                pass

    def _build_ui(self):
        frame = tk.Frame(self.root, padx=16, pady=16)
        frame.pack(fill="both", expand=True)

        min_delay_ms, max_delay_ms = self.app.get_click_delay_limits_ms()

        tk.Label(frame, text="点击频率（ms）").grid(row=0, column=0, sticky="w")
        tk.Entry(frame, textvariable=self.delay_var, width=18).grid(row=0, column=1, sticky="ew", padx=(8, 0))
        tk.Label(frame, text=f"范围：{min_delay_ms}-{max_delay_ms} ms").grid(row=0, column=2, sticky="w", padx=(8, 0))

        tk.Label(frame, text="VRChat 日志目录").grid(row=1, column=0, sticky="w", pady=(12, 0))
        tk.Entry(frame, textvariable=self.log_dir_var).grid(row=1, column=1, sticky="ew", padx=(8, 8), pady=(12, 0))
        tk.Button(frame, text="浏览", width=10, command=self._browse_log_dir).grid(row=1, column=2, sticky="ew", pady=(12, 0))

        tk.Label(frame, text=f"目标：{self.app.osc_client.host}:{self.app.osc_client.port}").grid(row=2, column=0, columnspan=3, sticky="w", pady=(12, 0))
        tk.Label(frame, text="热键：F1 开始，F2 停止").grid(row=3, column=0, columnspan=3, sticky="w", pady=(4, 0))

        button_frame = tk.Frame(frame)
        button_frame.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(16, 0))
        tk.Button(button_frame, text="开始", width=12, command=self._start_clicking).pack(side="left")
        tk.Button(button_frame, text="停止", width=12, command=self._stop_clicking).pack(side="left", padx=(12, 0))
        tk.Button(button_frame, text="统计", width=12, command=self.open_stats_page).pack(side="right")

        tk.Checkbutton(frame, text="自动监听最新日志并发送SP", variable=self.monitor_var, command=self._toggle_monitoring).grid(row=5, column=0, columnspan=3, sticky="w", pady=(12, 0))

        language_frame = tk.Frame(frame)
        language_frame.grid(row=6, column=0, columnspan=3, sticky="w", pady=(8, 0))
        tk.Label(language_frame, text="发送语言：").pack(side="left")
        tk.Checkbutton(language_frame, text="中文", variable=self.language_zh_var, command=lambda: self._on_language_toggle("zh")).pack(side="left")
        tk.Checkbutton(language_frame, text="英语", variable=self.language_en_var, command=lambda: self._on_language_toggle("en")).pack(side="left")
        tk.Checkbutton(language_frame, text="日语", variable=self.language_ja_var, command=lambda: self._on_language_toggle("ja")).pack(side="left")

        tk.Label(frame, textvariable=self.status_var, anchor="w", justify="left", wraplength=620).grid(row=7, column=0, columnspan=3, sticky="ew", pady=(16, 0))

        frame.columnconfigure(1, weight=1)

    def set_status(self, text):
        self.status_var.set(text)

    def _handle_window_close(self):
        if self.app.ensure_tray_started():
            self.hide_to_tray()
            return
        self.app.close_app()

    def _on_root_unmap(self, _event):
        if self.root.state() == "iconic" and self.app.ensure_tray_started():
            self.hide_to_tray()

    def _on_root_map(self, _event):
        self._is_hidden_to_tray = False

    def hide_to_tray(self):
        if self._is_hidden_to_tray and not self.root.winfo_viewable():
            return
        self._is_hidden_to_tray = True
        self.root.withdraw()
        self.set_status("状态：程序已最小化到托盘")

    def show_from_tray(self):
        self._is_hidden_to_tray = False
        self.root.deiconify()
        try:
            self.root.state("normal")
        except Exception:
            pass
        self.root.after(0, self._focus_window)

    def schedule_show_from_external_request(self):
        self.root.after(0, self.show_from_tray)

    def _focus_window(self):
        self.root.lift()
        try:
            self.root.attributes("-topmost", True)
            self.root.after(150, lambda: self.root.attributes("-topmost", False))
        except Exception:
            pass
        try:
            self.root.focus_force()
        except Exception:
            pass

    def exit_from_tray(self):
        self.app.close_app()

    def schedule_status(self, text):
        self.root.after(0, lambda: self.set_status(text))

    def apply_startup_monitoring_state(self, started, error_message=None):
        self.monitor_var.set(started)
        if not started and error_message:
            self.set_status(f"状态：{error_message}")

    def open_stats_page(self):
        try:
            self.app.open_stats_page()
        except Exception as exc:
            messagebox.showerror("错误", f"打开统计页面失败：{exc}")

    def _apply_click_delay(self, *_args):
        try:
            click_delay_ms = self.app.apply_click_delay(self.delay_var.get())
            self.app.save_click_delay_ms(click_delay_ms)
        except ValueError:
            return

    def _browse_log_dir(self):
        current_value = self.log_dir_var.get().strip()
        initial_dir = current_value if current_value else None
        selected_dir = filedialog.askdirectory(initialdir=initial_dir)
        if selected_dir:
            self.log_dir_var.set(selected_dir)
            self.app.save_log_dir(selected_dir)
            self.set_status(f"状态：已选择日志目录 {selected_dir}")

    def _start_clicking(self):
        try:
            self.app.start_clicking(self.delay_var.get())
        except ValueError as exc:
            messagebox.showerror("错误", str(exc))

    def _stop_clicking(self):
        self.app.stop_clicking()

    def get_selected_languages(self):
        languages = []
        if self.language_zh_var.get():
            languages.append("zh")
        if self.language_en_var.get():
            languages.append("en")
        if self.language_ja_var.get():
            languages.append("ja")
        return languages

    def _ensure_at_least_one_language(self, preferred_language=None):
        selected = self.get_selected_languages()
        if selected:
            return selected

        if preferred_language == "en":
            self.language_en_var.set(True)
        elif preferred_language == "ja":
            self.language_ja_var.set(True)
        else:
            self.language_zh_var.set(True)

        messagebox.showwarning("提示", "至少需要保留一种发送语言")
        return self.get_selected_languages()

    def _on_language_toggle(self, preferred_language):
        languages = self._ensure_at_least_one_language(preferred_language)
        self.app.save_languages(languages)

    def _toggle_monitoring(self):
        if self.monitor_var.get():
            try:
                selected_languages = self._ensure_at_least_one_language("zh")
                self.app.save_languages(selected_languages)
                self.app.start_monitoring(self.log_dir_var.get().strip(), selected_languages)
            except ValueError as exc:
                self.monitor_var.set(False)
                self.set_status(f"状态：{exc}")
                messagebox.showerror("错误", str(exc))
        else:
            self.app.stop_monitoring()

    def run(self):
        self.root.mainloop()
