import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SETTINGS_FILE = PROJECT_ROOT / "settings.json"


class SettingsStore:
    def __init__(self, file_path=SETTINGS_FILE):
        self.file_path = Path(file_path)

    def load(self):
        if not self.file_path.exists():
            return {}

        try:
            return json.loads(self.file_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def save(self, settings):
        self.file_path.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_log_dir(self):
        saved_log_dir = self.load().get("log_dir", "")
        if not saved_log_dir:
            return ""
        return str(Path(saved_log_dir))

    def set_log_dir(self, log_dir):
        self.save({"log_dir": log_dir})
