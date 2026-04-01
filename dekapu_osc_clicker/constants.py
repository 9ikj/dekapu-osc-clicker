import os
import sys
from pathlib import Path

BASE_APP_TITLE = "dekapu-osc-clicker"
APP_VERSION = os.getenv("DEKAPU_OSC_CLICKER_VERSION", "").strip()
APP_TITLE = f"{BASE_APP_TITLE} {APP_VERSION}" if APP_VERSION else BASE_APP_TITLE
WINDOW_SIZE = "720x320"


def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent


def get_assets_dir():
    return get_base_dir() / "assets"

VRCHAT_OSC_IP = "127.0.0.1"
VRCHAT_OSC_PORT = 9000
DEFAULT_CLICK_DELAY_MS = 200
DEFAULT_CLICK_PRESS_DURATION = 0.08
LOG_FILE_PATTERN = "output_log_*.txt"
LOG_URL_MARKER = "[DSM SaveURL] Generated URL:"
MONITOR_POLL_INTERVAL = 0.5
