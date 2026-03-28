import base64
import binascii
import json
from urllib.parse import parse_qs, urlparse

from .constants import LOG_URL_MARKER


def extract_last_generated_url(log_file):
    try:
        content = log_file.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise ValueError(f"读取日志失败：{exc}") from exc

    last_url = None
    for line in content.splitlines():
        if LOG_URL_MARKER not in line:
            continue
        last_url = line.split(LOG_URL_MARKER, 1)[1].strip()

    if not last_url:
        raise ValueError("最新日志中未找到 DSM SaveURL")

    return last_url


def extract_generated_url_from_line(line):
    if LOG_URL_MARKER not in line:
        return None

    url = line.split(LOG_URL_MARKER, 1)[1].strip()
    return url or None


def decode_data_to_json(data_value):
    padded = data_value + "=" * (-len(data_value) % 4)
    try:
        decoded = base64.b64decode(padded)
    except binascii.Error as exc:
        raise ValueError("data 字段不是有效的 base64") from exc

    try:
        return json.loads(decoded.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("data 字段解码后不是有效 JSON") from exc


def extract_sp_from_generated_url(url):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    data_values = query.get("data")
    if not data_values or not data_values[0]:
        raise ValueError("URL 中未找到 data 参数")

    payload = decode_data_to_json(data_values[0])
    if "sp" not in payload:
        raise ValueError("JSON 中未找到 sp 字段")

    return str(payload["sp"])
