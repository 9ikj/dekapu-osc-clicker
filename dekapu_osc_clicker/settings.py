import json
from pathlib import Path

from .constants import get_data_dir


MIN_CLICK_DELAY_MS = 10
MAX_CLICK_DELAY_MS = 60000
VALID_LANGUAGES = ("zh", "en", "ja")
DEFAULT_LANGUAGE_ORDER = ["zh", "en", "ja"]
DEFAULT_SETTINGS = {
    "log_dir": "",
    "click_delay_ms": 200,
    "languages": DEFAULT_LANGUAGE_ORDER[:],
    "send_enabled": True,
}


def get_settings_file():
    return Path(get_data_dir()) / "settings.json"


class SettingsStore:
    def __init__(self, file_path=None):
        self.file_path = Path(file_path) if file_path is not None else get_settings_file()

    def load(self):
        settings = DEFAULT_SETTINGS.copy()
        if not self.file_path.exists():
            return settings

        try:
            loaded = json.loads(self.file_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return settings

        if isinstance(loaded, dict):
            settings.update(loaded)
        return settings

    def save(self, settings):
        merged = DEFAULT_SETTINGS.copy()
        if isinstance(settings, dict):
            merged.update(settings)

        merged["click_delay_ms"] = self._sanitize_click_delay_ms(merged.get("click_delay_ms"))
        merged["languages"] = self._sanitize_languages(merged.get("languages"))
        merged["log_dir"] = str(merged.get("log_dir", "") or "")
        merged["send_enabled"] = bool(merged.get("send_enabled", True))

        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")

    def update(self, **kwargs):
        settings = self.load()
        settings.update(kwargs)
        self.save(settings)
        return settings

    @staticmethod
    def _sanitize_click_delay_ms(value):
        try:
            click_delay_ms = int(float(value))
        except (TypeError, ValueError):
            click_delay_ms = DEFAULT_SETTINGS["click_delay_ms"]
        return max(MIN_CLICK_DELAY_MS, min(MAX_CLICK_DELAY_MS, click_delay_ms))

    @staticmethod
    def _sanitize_languages(languages):
        if not isinstance(languages, list):
            return DEFAULT_LANGUAGE_ORDER[:]

        valid = []
        for lang in languages:
            if lang in VALID_LANGUAGES and lang not in valid:
                valid.append(lang)

        return valid or DEFAULT_LANGUAGE_ORDER[:]

    def get_log_dir(self):
        saved_log_dir = self.load().get("log_dir", "")
        if not saved_log_dir:
            return ""
        return str(Path(saved_log_dir))

    def set_log_dir(self, log_dir):
        self.update(log_dir=log_dir)

    def get_click_delay_ms(self):
        return self._sanitize_click_delay_ms(self.load().get("click_delay_ms", DEFAULT_SETTINGS["click_delay_ms"]))

    def set_click_delay_ms(self, click_delay_ms):
        self.update(click_delay_ms=self._sanitize_click_delay_ms(click_delay_ms))

    def get_languages(self):
        return self._sanitize_languages(self.load().get("languages", DEFAULT_SETTINGS["languages"]))

    def set_languages(self, languages):
        self.update(languages=self._sanitize_languages(languages))

    def get_send_enabled(self):
        return bool(self.load().get("send_enabled", DEFAULT_SETTINGS["send_enabled"]))

    def set_send_enabled(self, send_enabled):
        self.update(send_enabled=bool(send_enabled))
