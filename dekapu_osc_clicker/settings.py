import json
import sys
from pathlib import Path


def get_settings_file():
    if getattr(sys, "frozen", False):
        base_dir = Path(sys.executable).resolve().parent
    elif sys.argv and sys.argv[0]:
        base_dir = Path(sys.argv[0]).resolve().parent
    else:
        base_dir = Path.cwd()
    return base_dir / "settings.json"


class SettingsStore:
    def __init__(self, file_path=None):
        self.file_path = Path(file_path) if file_path is not None else get_settings_file()

    def load(self):
        if not self.file_path.exists():
            return {}

        try:
            return json.loads(self.file_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def save(self, settings):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_path.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_log_dir(self):
        saved_log_dir = self.load().get("log_dir", "")
        if not saved_log_dir:
            return ""
        return str(Path(saved_log_dir))

    def set_log_dir(self, log_dir):
        self.save({"log_dir": log_dir})
