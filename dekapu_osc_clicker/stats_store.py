import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path


TRACKED_FIELDS = (
    "credit",
    "credit_all",
    "sp",
    "sp_use",
    "playtime",
    "firstboot",
    "lastsave",
    "version",
)

HOURLY_CHANGE_FIELDS = ("credit", "credit_all", "sp", "sp_use")


class StatsStore:
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self):
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS payload_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    captured_at TEXT NOT NULL,
                    captured_hour TEXT NOT NULL,
                    source_log_file TEXT,
                    source_url TEXT,
                    payload_hash TEXT NOT NULL UNIQUE,
                    payload_json TEXT NOT NULL,
                    credit INTEGER,
                    credit_all INTEGER,
                    sp INTEGER,
                    sp_use INTEGER,
                    playtime INTEGER,
                    firstboot TEXT,
                    lastsave TEXT,
                    version INTEGER
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_payload_snapshots_captured_at ON payload_snapshots(captured_at)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_payload_snapshots_captured_hour ON payload_snapshots(captured_hour)"
            )

    @staticmethod
    def _normalize_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _normalize_text(value):
        if value is None:
            return None
        return str(value)

    @staticmethod
    def _row_to_dict(row):
        return dict(row) if row is not None else None

    def record_payload(self, payload, source_log_file=None, source_url=None, captured_at=None):
        if not isinstance(payload, dict):
            raise ValueError("payload 必须是字典")

        now = captured_at or datetime.now()
        if isinstance(now, str):
            now = datetime.fromisoformat(now)

        captured_at_text = now.strftime("%Y-%m-%d %H:%M:%S")
        captured_hour = now.strftime("%Y-%m-%d %H:00:00")
        payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()

        values = {
            "captured_at": captured_at_text,
            "captured_hour": captured_hour,
            "source_log_file": self._normalize_text(source_log_file),
            "source_url": self._normalize_text(source_url),
            "payload_hash": payload_hash,
            "payload_json": payload_json,
            "credit": self._normalize_int(payload.get("credit")),
            "credit_all": self._normalize_int(payload.get("credit_all")),
            "sp": self._normalize_int(payload.get("sp")),
            "sp_use": self._normalize_int(payload.get("sp_use")),
            "playtime": self._normalize_int(payload.get("playtime")),
            "firstboot": self._normalize_text(payload.get("firstboot")),
            "lastsave": self._normalize_text(payload.get("lastsave")),
            "version": self._normalize_int(payload.get("version")),
        }

        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO payload_snapshots (
                    captured_at,
                    captured_hour,
                    source_log_file,
                    source_url,
                    payload_hash,
                    payload_json,
                    credit,
                    credit_all,
                    sp,
                    sp_use,
                    playtime,
                    firstboot,
                    lastsave,
                    version
                ) VALUES (
                    :captured_at,
                    :captured_hour,
                    :source_log_file,
                    :source_url,
                    :payload_hash,
                    :payload_json,
                    :credit,
                    :credit_all,
                    :sp,
                    :sp_use,
                    :playtime,
                    :firstboot,
                    :lastsave,
                    :version
                )
                """,
                values,
            )
            return cursor.rowcount > 0

    def get_today_summary(self, day=None):
        day_text = day or datetime.now().strftime("%Y-%m-%d")
        day_start = f"{day_text} 00:00:00"
        day_end = f"{day_text} 23:59:59"

        with self._connect() as connection:
            first_row = connection.execute(
                """
                SELECT captured_at, credit
                FROM payload_snapshots
                WHERE captured_at BETWEEN ? AND ? AND credit IS NOT NULL
                ORDER BY captured_at ASC, id ASC
                LIMIT 1
                """,
                (day_start, day_end),
            ).fetchone()
            last_row = connection.execute(
                """
                SELECT captured_at, credit
                FROM payload_snapshots
                WHERE captured_at BETWEEN ? AND ? AND credit IS NOT NULL
                ORDER BY captured_at DESC, id DESC
                LIMIT 1
                """,
                (day_start, day_end),
            ).fetchone()
            total_snapshots = connection.execute(
                "SELECT COUNT(*) FROM payload_snapshots WHERE captured_at BETWEEN ? AND ?",
                (day_start, day_end),
            ).fetchone()[0]

        first_credit = self._normalize_int(first_row["credit"] if first_row else None) or 0
        last_credit = self._normalize_int(last_row["credit"] if last_row else None) or 0
        return {
            "date": day_text,
            "total_credit_gained": max(0, last_credit - first_credit),
            "first_credit": first_credit if first_row else None,
            "last_credit": last_credit if last_row else None,
            "first_captured_at": first_row["captured_at"] if first_row else None,
            "last_captured_at": last_row["captured_at"] if last_row else None,
            "snapshot_count": total_snapshots,
        }

    def get_today_sp_used(self, current_sp, day=None):
        day_text = day or datetime.now().strftime("%Y-%m-%d")
        day_start = f"{day_text} 00:00:00"
        day_end = f"{day_text} 23:59:59"
        current_sp_value = self._normalize_int(current_sp)
        if current_sp_value is None:
            return 0

        with self._connect() as connection:
            first_row = connection.execute(
                """
                SELECT sp
                FROM payload_snapshots
                WHERE captured_at BETWEEN ? AND ? AND sp IS NOT NULL
                ORDER BY captured_at ASC, id ASC
                LIMIT 1
                """,
                (day_start, day_end),
            ).fetchone()

        first_sp = self._normalize_int(first_row["sp"] if first_row else None)
        if first_sp is None:
            return 0
        return max(0, first_sp - current_sp_value)

    def get_hourly_credit(self, day=None):
        return self._get_hourly_changes(("credit",), day=day)

    def get_hourly_changes(self, fields=None, day=None):
        requested_fields = tuple(fields or HOURLY_CHANGE_FIELDS)
        return self._get_hourly_changes(requested_fields, day=day)

    def _get_hourly_changes(self, fields, day=None):
        valid_fields = [field for field in fields if field in HOURLY_CHANGE_FIELDS or field == "credit"]
        if not valid_fields:
            valid_fields = ["credit"]

        day_text = day or datetime.now().strftime("%Y-%m-%d")
        day_start = f"{day_text} 00:00:00"
        day_end = f"{day_text} 23:59:59"
        select_fields = ", ".join(valid_fields)
        hour_buckets = {
            f"{day_text} {hour:02d}:00:00": {"hour": f"{hour:02d}:00", "captured_hour": f"{day_text} {hour:02d}:00:00"}
            for hour in range(24)
        }
        for row in hour_buckets.values():
            for field in valid_fields:
                row[field] = 0

        with self._connect() as connection:
            snapshots = connection.execute(
                f"""
                SELECT captured_hour, {select_fields}
                FROM payload_snapshots
                WHERE captured_at BETWEEN ? AND ?
                ORDER BY captured_at ASC, id ASC
                """,
                (day_start, day_end),
            ).fetchall()

        first_values = {}
        last_values = {}
        for snapshot in snapshots:
            hour_key = snapshot["captured_hour"]
            if hour_key not in hour_buckets:
                continue
            for field in valid_fields:
                value = self._normalize_int(snapshot[field])
                if value is None:
                    continue
                first_values.setdefault(hour_key, {}).setdefault(field, value)
                last_values.setdefault(hour_key, {})[field] = value

        for hour_key, row in hour_buckets.items():
            for field in valid_fields:
                first_value = first_values.get(hour_key, {}).get(field)
                last_value = last_values.get(hour_key, {}).get(field)
                if first_value is None or last_value is None:
                    row[field] = 0
                else:
                    row[field] = max(0, last_value - first_value)

        return {"date": day_text, "fields": valid_fields, "rows": list(hour_buckets.values())}

    def get_recent_snapshots(self, limit=50):
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT captured_at, source_log_file, credit, credit_all, sp, sp_use, playtime, firstboot, lastsave, version
                FROM payload_snapshots
                ORDER BY captured_at DESC, id DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()
        return [self._row_to_dict(row) for row in rows]
