import io
import threading

from .constants import get_assets_dir
from .icon_data import get_tray_icon_image, get_window_icon_png_bytes

try:
    import pystray
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover - optional runtime dependency
    pystray = None
    Image = None
    ImageDraw = None
    ImageFont = None


class TrayController:
    def __init__(self, ui):
        self.ui = ui
        self.icon = None
        self.thread = None
        self._lock = threading.Lock()
        self._running = False

    @staticmethod
    def is_supported():
        return pystray is not None and Image is not None

    def _create_fallback_icon(self):
        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((4, 4, 60, 60), radius=16, fill=(126, 179, 255, 255))
        draw.rounded_rectangle((12, 12, 52, 44), radius=10, fill=(255, 255, 255, 255))
        draw.ellipse((42, 42, 54, 54), fill=(255, 230, 120, 255))
        font = ImageFont.load_default()
        draw.text((20, 22), "SP", fill=(95, 116, 255, 255), font=font)
        return image

    def _load_icon_image(self):
        png_path = get_assets_dir() / "sp_assistant_icon.png"
        if Image is None:
            return None

        try:
            return Image.open(io.BytesIO(get_window_icon_png_bytes()))
        except Exception:
            pass

        if png_path.exists():
            try:
                return Image.open(png_path)
            except Exception:
                pass

        try:
            return get_tray_icon_image(64)
        except Exception:
            return self._create_fallback_icon()

    def _show_window(self, icon=None, item=None):
        self.ui.show_from_tray()

    def _hide_window(self, icon=None, item=None):
        self.ui.hide_to_tray()

    def _open_stats(self, icon=None, item=None):
        self.ui.open_stats_page()

    def _exit_app(self, icon=None, item=None):
        self.ui.exit_from_tray()

    def _run_icon(self):
        image = self._load_icon_image()
        menu = pystray.Menu(
            pystray.MenuItem("打开", self._show_window, default=True),
            pystray.MenuItem("隐藏", self._hide_window),
            pystray.MenuItem("统计", self._open_stats),
            pystray.MenuItem("退出", self._exit_app),
        )
        self.icon = pystray.Icon("dekapu-osc-clicker", image, "SP 小助手", menu)
        self._running = True
        self.icon.run()

    def ensure_started(self):
        if not self.is_supported():
            return False
        with self._lock:
            if self.thread and self.thread.is_alive():
                return True
            self.thread = threading.Thread(target=self._run_icon, daemon=True)
            self.thread.start()
            return True

    def stop(self):
        with self._lock:
            icon = self.icon
            self.icon = None
            self._running = False
        if icon is not None:
            try:
                icon.stop()
            except Exception:
                pass
