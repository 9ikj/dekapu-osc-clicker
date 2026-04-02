try:
    import ctypes
    from ctypes import wintypes
except Exception:  # pragma: no cover
    ctypes = None
    wintypes = None

ERROR_ALREADY_EXISTS = 183
MUTEX_NAME = "Local\\DekapuOscClickerSingleton"
WINDOW_TITLE = "dekapu-osc-clicker"
SW_SHOWNORMAL = 1
SW_RESTORE = 9


class SingleInstanceManager:
    def __init__(self, window_title=WINDOW_TITLE):
        self.window_title = window_title
        self._mutex_handle = None
        self.is_primary_instance = False

    def start(self):
        mutex_result = self._acquire_windows_mutex()
        if mutex_result is False:
            self.is_primary_instance = False
            return False
        self._mutex_handle = mutex_result
        self.is_primary_instance = True
        return True

    def _acquire_windows_mutex(self):
        if ctypes is None or wintypes is None:
            return None
        try:
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
            kernel32.CreateMutexW.restype = wintypes.HANDLE
            kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
            kernel32.CloseHandle.restype = wintypes.BOOL

            ctypes.set_last_error(0)
            handle = kernel32.CreateMutexW(None, False, MUTEX_NAME)
            if not handle:
                return None

            last_error = ctypes.get_last_error()
            if last_error == ERROR_ALREADY_EXISTS:
                kernel32.CloseHandle(handle)
                return False
            return handle
        except Exception:
            return None

    def notify_existing_instance(self):
        return self._bring_existing_window_to_front()

    def _bring_existing_window_to_front(self):
        if ctypes is None or wintypes is None:
            return False
        try:
            user32 = ctypes.WinDLL("user32", use_last_error=True)
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

            WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
            user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
            user32.EnumWindows.restype = wintypes.BOOL
            user32.IsWindowVisible.argtypes = [wintypes.HWND]
            user32.IsWindowVisible.restype = wintypes.BOOL
            user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
            user32.GetWindowTextLengthW.restype = ctypes.c_int
            user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
            user32.GetWindowTextW.restype = ctypes.c_int
            user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
            user32.ShowWindow.restype = wintypes.BOOL
            user32.BringWindowToTop.argtypes = [wintypes.HWND]
            user32.BringWindowToTop.restype = wintypes.BOOL
            user32.SetForegroundWindow.argtypes = [wintypes.HWND]
            user32.SetForegroundWindow.restype = wintypes.BOOL
            user32.GetForegroundWindow.argtypes = []
            user32.GetForegroundWindow.restype = wintypes.HWND
            user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
            user32.GetWindowThreadProcessId.restype = wintypes.DWORD
            user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
            user32.AttachThreadInput.restype = wintypes.BOOL
            kernel32.GetCurrentThreadId.argtypes = []
            kernel32.GetCurrentThreadId.restype = wintypes.DWORD

            matched_hwnd = None
            title_prefix = self.window_title.lower()

            def enum_proc(hwnd, _lparam):
                nonlocal matched_hwnd
                length = user32.GetWindowTextLengthW(hwnd)
                if length <= 0:
                    return True
                buffer = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buffer, length + 1)
                title = buffer.value.strip().lower()
                if not title or not title.startswith(title_prefix):
                    return True
                matched_hwnd = hwnd
                return False

            user32.EnumWindows(WNDENUMPROC(enum_proc), 0)
            hwnd = matched_hwnd
            if not hwnd:
                return False

            user32.ShowWindow(hwnd, SW_RESTORE)
            user32.ShowWindow(hwnd, SW_SHOWNORMAL)

            foreground = user32.GetForegroundWindow()
            current_thread = kernel32.GetCurrentThreadId()
            target_thread = user32.GetWindowThreadProcessId(hwnd, None)
            foreground_thread = user32.GetWindowThreadProcessId(foreground, None) if foreground else 0

            attached_foreground = False
            attached_target = False
            try:
                if foreground_thread and foreground_thread != current_thread:
                    attached_foreground = bool(user32.AttachThreadInput(current_thread, foreground_thread, True))
                if target_thread and target_thread != current_thread:
                    attached_target = bool(user32.AttachThreadInput(current_thread, target_thread, True))

                user32.BringWindowToTop(hwnd)
                user32.SetForegroundWindow(hwnd)
            finally:
                if attached_target:
                    user32.AttachThreadInput(current_thread, target_thread, False)
                if attached_foreground:
                    user32.AttachThreadInput(current_thread, foreground_thread, False)
            return True
        except Exception:
            return False

    def stop(self):
        if self._mutex_handle and ctypes is not None:
            try:
                kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
                kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
                kernel32.CloseHandle.restype = wintypes.BOOL
                kernel32.CloseHandle(self._mutex_handle)
            except Exception:
                pass
        self._mutex_handle = None
