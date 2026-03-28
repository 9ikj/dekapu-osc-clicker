import tkinter as tk
from tkinter import filedialog, messagebox

from .constants import APP_TITLE, DEFAULT_CLICK_DELAY, WINDOW_SIZE


class MainWindow:
    def __init__(self, app_controller):
        self.app = app_controller
        self.root = tk.Tk()
        self.root.title(APP_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.resizable(False, False)

        self.delay_var = tk.StringVar(value=str(DEFAULT_CLICK_DELAY))
        self.log_dir_var = tk.StringVar(value=self.app.get_saved_log_dir())
        self.monitor_var = tk.BooleanVar(value=False)
        self.language_zh_var = tk.BooleanVar(value=True)
        self.language_en_var = tk.BooleanVar(value=True)
        self.language_ja_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value="状态：已停止")

        self._build_ui()
        self.delay_var.trace_add("write", self._apply_click_delay)
        self.root.protocol("WM_DELETE_WINDOW", self.app.close_app)

    def _build_ui(self):
        frame = tk.Frame(self.root, padx=16, pady=16)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="点击间隔（秒）").grid(row=0, column=0, sticky="w")
        tk.Entry(frame, textvariable=self.delay_var, width=18).grid(row=0, column=1, sticky="ew", padx=(8, 0))

        tk.Label(frame, text="VRChat 日志目录").grid(row=1, column=0, sticky="w", pady=(12, 0))
        tk.Entry(frame, textvariable=self.log_dir_var).grid(row=1, column=1, sticky="ew", padx=(8, 8), pady=(12, 0))
        tk.Button(frame, text="浏览", width=10, command=self._browse_log_dir).grid(row=1, column=2, sticky="ew", pady=(12, 0))

        tk.Label(frame, text=f"目标：{self.app.osc_client.host}:{self.app.osc_client.port}").grid(row=2, column=0, columnspan=3, sticky="w", pady=(12, 0))
        tk.Label(frame, text="热键：F1 开始，F2 停止").grid(row=3, column=0, columnspan=3, sticky="w", pady=(4, 0))

        button_frame = tk.Frame(frame)
        button_frame.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(16, 0))
        tk.Button(button_frame, text="开始", width=12, command=self._start_clicking).pack(side="left")
        tk.Button(button_frame, text="停止", width=12, command=self._stop_clicking).pack(side="left", padx=(12, 0))

        tk.Checkbutton(frame, text="自动监听最新日志并发送SP", variable=self.monitor_var, command=self._toggle_monitoring).grid(row=5, column=0, columnspan=3, sticky="w", pady=(12, 0))

        language_frame = tk.Frame(frame)
        language_frame.grid(row=6, column=0, columnspan=3, sticky="w", pady=(8, 0))
        tk.Label(language_frame, text="发送语言：").pack(side="left")
        tk.Checkbutton(language_frame, text="中文", variable=self.language_zh_var).pack(side="left")
        tk.Checkbutton(language_frame, text="英语", variable=self.language_en_var).pack(side="left")
        tk.Checkbutton(language_frame, text="日语", variable=self.language_ja_var).pack(side="left")

        tk.Label(frame, textvariable=self.status_var, anchor="w", justify="left", wraplength=490).grid(row=7, column=0, columnspan=3, sticky="ew", pady=(16, 0))

        frame.columnconfigure(1, weight=1)

    def set_status(self, text):
        self.status_var.set(text)

    def schedule_status(self, text):
        self.root.after(0, lambda: self.set_status(text))

    def _apply_click_delay(self, *_args):
        try:
            self.app.apply_click_delay(self.delay_var.get())
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

    def _toggle_monitoring(self):
        if self.monitor_var.get():
            try:
                self.app.start_monitoring(self.log_dir_var.get().strip(), self.get_selected_languages())
            except ValueError as exc:
                self.monitor_var.set(False)
                self.set_status(f"状态：{exc}")
                messagebox.showerror("错误", str(exc))
        else:
            self.app.stop_monitoring()

    def run(self):
        self.root.mainloop()
