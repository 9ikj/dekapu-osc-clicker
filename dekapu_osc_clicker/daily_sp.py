import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


SHANGHAI_TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")
DEFAULT_DAILY_SP = {
    "date": "",
    "first_sp": 0,
    "last_sp": 0,
}


def get_daily_sp_file():
    if getattr(sys, "frozen", False):
        base_dir = Path(sys.executable).resolve().parent
    elif sys.argv and sys.argv[0]:
        base_dir = Path(sys.argv[0]).resolve().parent
    else:
        base_dir = Path.cwd()
    return base_dir / "daily_sp.json"


class DailySPTracker:
    def __init__(self, file_path=None):
        self.file_path = Path(file_path) if file_path is not None else get_daily_sp_file()

    @staticmethod
    def today_string():
        return datetime.now(SHANGHAI_TZ).strftime("%Y-%m-%d")

    def load(self):
        if not self.file_path.exists():
            return DEFAULT_DAILY_SP.copy()

        try:
            data = json.loads(self.file_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return DEFAULT_DAILY_SP.copy()

        if not isinstance(data, dict):
            return DEFAULT_DAILY_SP.copy()

        merged = DEFAULT_DAILY_SP.copy()
        merged.update(data)
        return merged

    def save(self, data):
        merged = DEFAULT_DAILY_SP.copy()
        if isinstance(data, dict):
            merged.update(data)

        merged["date"] = str(merged.get("date", "") or "")
        merged["first_sp"] = self._to_int(merged.get("first_sp"))
        merged["last_sp"] = self._to_int(merged.get("last_sp"))

        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _to_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def update(self, sp_value):
        current_sp = self._to_int(sp_value)
        today = self.today_string()
        data = self.load()

        if data.get("date") != today:
            data = {
                "date": today,
                "first_sp": current_sp,
                "last_sp": current_sp,
            }
        else:
            first_sp = self._to_int(data.get("first_sp"))
            if first_sp <= 0:
                first_sp = current_sp
            data = {
                "date": today,
                "first_sp": first_sp,
                "last_sp": current_sp,
            }

        self.save(data)
        today_used = max(0, self._to_int(data["first_sp"]) - current_sp)
        return data, today_used
