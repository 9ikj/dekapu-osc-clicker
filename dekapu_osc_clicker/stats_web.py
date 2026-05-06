import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .constants import STATS_WEB_PORT


class StatsWebServer:
    def __init__(self, stats_store, get_bind_host=None):
        self.stats_store = stats_store
        self.get_bind_host = get_bind_host or (lambda: "127.0.0.1")
        self.server = None
        self.thread = None
        self._lock = threading.Lock()
        self._templates_dir = Path(__file__).resolve().parent / "templates"

    def ensure_started(self):
        with self._lock:
            if self.server is not None:
                return self.base_url

            handler = self._build_handler()
            bind_host = self.get_bind_host()
            self.server = ThreadingHTTPServer((bind_host, STATS_WEB_PORT), handler)
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            return self.base_url

    @property
    def base_url(self):
        if self.server is None:
            raise RuntimeError("统计服务尚未启动")
        host, port = self.server.server_address
        # 如果绑定到 0.0.0.0，返回 127.0.0.1 用于本地打开
        if host == "0.0.0.0":
            host = "127.0.0.1"
        return f"http://{host}:{port}"

    def open_page(self, path="/"):
        base_url = self.ensure_started()
        webbrowser.open(f"{base_url}{path}")
        return f"{base_url}{path}"

    def stop(self):
        with self._lock:
            server = self.server
            thread = self.thread
            self.server = None
            self.thread = None
        if server is not None:
            server.shutdown()
            server.server_close()
        if thread is not None and thread.is_alive():
            thread.join(timeout=1)

    def _read_template(self, name):
        template_path = self._templates_dir / name
        return template_path.read_text(encoding="utf-8")

    def _build_handler(self):
        stats_store = self.stats_store
        index_html = self._read_template("index.html")
        changes_html = self._read_template("changes.html")

        class StatsHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                parsed = urlparse(self.path)
                if parsed.path == "/":
                    self._send_html(index_html)
                    return
                if parsed.path == "/changes":
                    self._send_html(changes_html)
                    return
                if parsed.path == "/api/today-summary":
                    params = parse_qs(parsed.query)
                    day = params.get("day", [None])[0]
                    self._send_json(stats_store.get_today_summary(day=day))
                    return
                if parsed.path == "/api/hourly-credit":
                    params = parse_qs(parsed.query)
                    day = params.get("day", [None])[0]
                    self._send_json(stats_store.get_hourly_credit(day=day))
                    return
                if parsed.path == "/api/hourly-changes":
                    params = parse_qs(parsed.query)
                    day = params.get("day", [None])[0]
                    fields = params.get("fields", [""])[0].split(",") if "fields" in params else None
                    self._send_json(stats_store.get_hourly_changes(fields=fields, day=day))
                    return
                if parsed.path == "/api/hourly-values":
                    params = parse_qs(parsed.query)
                    day = params.get("day", [None])[0]
                    fields = params.get("fields", [""])[0].split(",") if "fields" in params else None
                    self._send_json(stats_store.get_hourly_values(fields=fields, day=day))
                    return
                self.send_error(404)

            def log_message(self, format, *args):
                return

            def _send_html(self, content):
                data = content.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _send_json(self, payload):
                data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        return StatsHandler
