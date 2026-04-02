import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


class StatsWebServer:
    def __init__(self, stats_store):
        self.stats_store = stats_store
        self.server = None
        self.thread = None
        self._lock = threading.Lock()

    def ensure_started(self):
        with self._lock:
            if self.server is not None:
                return self.base_url

            handler = self._build_handler()
            self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            return self.base_url

    @property
    def base_url(self):
        if self.server is None:
            raise RuntimeError("统计服务尚未启动")
        host, port = self.server.server_address
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

    def _build_handler(self):
        stats_store = self.stats_store

        class StatsHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                parsed = urlparse(self.path)
                if parsed.path == "/":
                    self._send_html(_build_index_html())
                    return
                if parsed.path == "/changes":
                    self._send_html(_build_changes_html())
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


def _build_index_html():
    return """<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>统计</title>
  <style>
    :root {
      --bg: #09111f;
      --panel: rgba(16, 24, 40, 0.78);
      --panel-border: rgba(148, 163, 184, 0.14);
      --text: #e5eefc;
      --muted: #9fb0c9;
      --primary: #60a5fa;
      --primary-strong: #3b82f6;
      --accent: #34d399;
      --shadow: 0 20px 50px rgba(0, 0, 0, 0.28);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: var(--text);
      font-family: \"Segoe UI\", \"Microsoft YaHei\", Arial, sans-serif;
      background:
        radial-gradient(circle at top left, rgba(59,130,246,0.20), transparent 28%),
        radial-gradient(circle at top right, rgba(52,211,153,0.14), transparent 24%),
        linear-gradient(180deg, #0a1221 0%, #08101d 100%);
      min-height: 100vh;
    }
    .wrap { max-width: 1180px; margin: 0 auto; padding: 28px; }
    .hero {
      display: flex; justify-content: space-between; gap: 16px; align-items: center;
      margin-bottom: 20px; padding: 24px 26px;
      border: 1px solid var(--panel-border); border-radius: 24px;
      background: linear-gradient(135deg, rgba(17,24,39,0.88), rgba(15,23,42,0.72));
      box-shadow: var(--shadow); backdrop-filter: blur(16px);
    }
    .hero-title { font-size: 28px; font-weight: 700; margin: 0 0 6px; }
    .hero-subtitle { color: var(--muted); margin: 0; }
    .row { display: flex; gap: 14px; align-items: center; flex-wrap: wrap; }
    .nav a, .switch button {
      color: var(--text); background: rgba(51,65,85,0.68); border: 1px solid rgba(148,163,184,0.16);
      padding: 10px 15px; border-radius: 999px; cursor: pointer; text-decoration: none;
      transition: all .18s ease;
    }
    .nav a:hover, .switch button:hover { transform: translateY(-1px); background: rgba(71,85,105,0.8); }
    .switch button.active {
      background: linear-gradient(135deg, var(--primary-strong), var(--primary));
      border-color: rgba(96,165,250,0.5);
      box-shadow: 0 10px 25px rgba(59,130,246,0.28);
    }
    .grid { display: grid; grid-template-columns: 320px 1fr; gap: 20px; }
    .card {
      background: var(--panel); border: 1px solid var(--panel-border); border-radius: 24px;
      padding: 24px; box-shadow: var(--shadow); backdrop-filter: blur(14px);
    }
    .metric-label { color: var(--muted); font-size: 14px; }
    .metric-value { font-size: 42px; font-weight: 800; margin-top: 10px; letter-spacing: .5px; }
    .metric-sub { margin-top: 12px; color: var(--muted); line-height: 1.7; }
    .status-dot {
      display: inline-block; width: 8px; height: 8px; border-radius: 999px; margin-right: 8px;
      background: var(--accent); box-shadow: 0 0 16px rgba(52,211,153,0.8);
    }
    .chart-title { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 16px; }
    .chart-title h2 { margin: 0; font-size: 22px; }
    .chart-shell {
      border-radius: 20px; padding: 16px; min-height: 460px;
      background: linear-gradient(180deg, rgba(8,15,28,0.95), rgba(11,19,35,0.82));
      border: 1px solid rgba(148,163,184,0.10);
    }
    svg { width: 100%; height: 420px; display: block; }
    .empty {
      min-height: 420px; display: flex; align-items: center; justify-content: center; text-align: center;
      color: var(--muted); font-size: 16px;
      border: 1px dashed rgba(148,163,184,0.18); border-radius: 16px;
      background: rgba(15,23,42,0.45);
    }
    @media (max-width: 900px) {
      .grid { grid-template-columns: 1fr; }
      .hero { flex-direction: column; align-items: flex-start; }
      .metric-value { font-size: 34px; }
    }
  </style>
</head>
<body>
  <div class=\"wrap\">
    <section class=\"hero\">
      <div>
        <h1 class=\"hero-title\">实时统计面板</h1>
        <p class=\"hero-subtitle\">自动刷新今日 credit 进度与每小时变化</p>
      </div>
      <div class=\"row nav\">
        <a href=\"/\">首页</a>
        <a href=\"/changes\">每小时变化</a>
      </div>
    </section>

    <section class=\"grid\">
      <div class=\"card\">
        <div class=\"metric-label\">今日获取的总 credit</div>
        <div id=\"totalCredit\" class=\"metric-value\">加载中...</div>
        <div id=\"summaryMeta\" class=\"metric-sub\"></div>
        <div id=\"lastUpdated\" class=\"metric-sub\"><span class=\"status-dot\"></span>最后更新时间：--</div>
      </div>

      <div class=\"card\">
        <div class=\"chart-title\">
          <h2>每小时 credit</h2>
          <div class=\"row switch\">
            <button id=\"barBtn\" class=\"active\">柱状图</button>
            <button id=\"lineBtn\">折线图</button>
          </div>
        </div>
        <div class=\"chart-shell\">
          <svg id=\"chart\" viewBox=\"0 0 1000 420\" preserveAspectRatio=\"none\"></svg>
          <div id=\"chartEmpty\" class=\"empty\" style=\"display:none;\">暂无统计数据，等待新日志...</div>
        </div>
      </div>
    </section>
  </div>
  <script>
    let chartMode = 'bar';
    let isRefreshing = false;
    let currentTotalCredit = 0;

    function formatNumber(value) {
      return new Intl.NumberFormat('zh-CN').format(Number(value || 0));
    }

    function animateNumber(elementId, fromValue, toValue, duration = 600) {
      const element = document.getElementById(elementId);
      const start = performance.now();
      const startValue = Number(fromValue || 0);
      const endValue = Number(toValue || 0);

      function frame(now) {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const value = Math.round(startValue + (endValue - startValue) * eased);
        element.textContent = formatNumber(value);
        if (progress < 1) {
          requestAnimationFrame(frame);
        }
      }

      requestAnimationFrame(frame);
    }

    function updateLastUpdated() {
      const now = new Date();
      document.getElementById('lastUpdated').innerHTML = `<span class=\"status-dot\"></span>最后更新时间：${now.toLocaleTimeString('zh-CN')}`;
    }

    function setMode(mode) {
      chartMode = mode;
      document.getElementById('barBtn').classList.toggle('active', mode === 'bar');
      document.getElementById('lineBtn').classList.toggle('active', mode === 'line');
      refreshDashboard();
    }

    async function loadSummary() {
      const response = await fetch('/api/today-summary');
      const data = await response.json();
      const nextTotalCredit = Number(data.total_credit_gained || 0);
      animateNumber('totalCredit', currentTotalCredit, nextTotalCredit);
      currentTotalCredit = nextTotalCredit;
      document.getElementById('summaryMeta').innerHTML = `快照 ${data.snapshot_count || 0} 条<br>首条：${data.first_captured_at || '--'}<br>末条：${data.last_captured_at || '--'}`;
      return data;
    }

    function renderBarChart(rows) {
      const svg = document.getElementById('chart');
      const width = 1000;
      const height = 420;
      const padding = 42;
      const values = rows.map(row => Number(row.credit || 0));
      const maxValue = Math.max(...values, 1);
      const innerWidth = width - padding * 2;
      const innerHeight = height - padding * 2;
      const barWidth = innerWidth / rows.length;
      let out = `
        <defs>
          <linearGradient id=\"barGradient\" x1=\"0\" y1=\"0\" x2=\"0\" y2=\"1\">
            <stop offset=\"0%\" stop-color=\"#60a5fa\" />
            <stop offset=\"100%\" stop-color=\"#2563eb\" />
          </linearGradient>
        </defs>
      `;
      for (let i = 0; i < 5; i += 1) {
        const y = padding + (innerHeight / 4) * i;
        out += `<line x1=\"${padding}\" y1=\"${y}\" x2=\"${width-padding}\" y2=\"${y}\" stroke=\"rgba(148,163,184,0.12)\" />`;
      }
      rows.forEach((row, index) => {
        const x = padding + index * barWidth + 5;
        const barHeight = (Number(row.credit || 0) / maxValue) * (innerHeight - 20);
        const y = height - padding - barHeight;
        const labelX = x + Math.max(barWidth - 10, 10) / 2;
        out += `<rect x=\"${x}\" y=\"${y}\" width=\"${Math.max(barWidth - 10, 10)}\" height=\"${barHeight}\" fill=\"url(#barGradient)\" rx=\"8\" />`;
        out += `<text x=\"${labelX}\" y=\"${height-padding+18}\" fill=\"#94a3b8\" font-size=\"10\" text-anchor=\"middle\">${row.hour.slice(0,2)}</text>`;
      });
      svg.innerHTML = out;
    }

    function renderLineChart(rows) {
      const svg = document.getElementById('chart');
      const width = 1000;
      const height = 420;
      const padding = 42;
      const values = rows.map(row => Number(row.credit || 0));
      const maxValue = Math.max(...values, 1);
      const innerWidth = width - padding * 2;
      const innerHeight = height - padding * 2;
      const stepX = innerWidth / Math.max(rows.length - 1, 1);
      const points = rows.map((row, index) => {
        const x = padding + index * stepX;
        const y = height - padding - (Number(row.credit || 0) / maxValue) * (innerHeight - 20);
        return { x, y, label: row.hour.slice(0,2) };
      });
      let out = `
        <defs>
          <linearGradient id=\"lineArea\" x1=\"0\" y1=\"0\" x2=\"0\" y2=\"1\">
            <stop offset=\"0%\" stop-color=\"rgba(52,211,153,0.35)\" />
            <stop offset=\"100%\" stop-color=\"rgba(52,211,153,0.02)\" />
          </linearGradient>
        </defs>
      `;
      for (let i = 0; i < 5; i += 1) {
        const y = padding + (innerHeight / 4) * i;
        out += `<line x1=\"${padding}\" y1=\"${y}\" x2=\"${width-padding}\" y2=\"${y}\" stroke=\"rgba(148,163,184,0.12)\" />`;
      }
      const areaPoints = [`${padding},${height-padding}`, ...points.map(p => `${p.x},${p.y}`), `${width-padding},${height-padding}`].join(' ');
      out += `<polygon fill=\"url(#lineArea)\" points=\"${areaPoints}\" />`;
      out += `<polyline fill=\"none\" stroke=\"#34d399\" stroke-width=\"4\" stroke-linejoin=\"round\" stroke-linecap=\"round\" points=\"${points.map(p => `${p.x},${p.y}`).join(' ')}\" />`;
      points.forEach(point => {
        out += `<circle cx=\"${point.x}\" cy=\"${point.y}\" r=\"4.5\" fill=\"#34d399\" />`;
        out += `<circle cx=\"${point.x}\" cy=\"${point.y}\" r=\"10\" fill=\"rgba(52,211,153,0.10)\" />`;
        out += `<text x=\"${point.x}\" y=\"${height-padding+18}\" fill=\"#94a3b8\" font-size=\"10\" text-anchor=\"middle\">${point.label}</text>`;
      });
      svg.innerHTML = out;
    }

    async function loadChart() {
      const response = await fetch('/api/hourly-credit');
      const data = await response.json();
      const rows = data.rows || [];
      const hasData = rows.some(row => Number(row.credit || 0) > 0);
      document.getElementById('chart').style.display = hasData ? 'block' : 'none';
      document.getElementById('chartEmpty').style.display = hasData ? 'none' : 'flex';
      if (!hasData) {
        return;
      }
      if (chartMode === 'line') {
        renderLineChart(rows);
      } else {
        renderBarChart(rows);
      }
    }

    async function refreshDashboard() {
      if (isRefreshing) {
        return;
      }
      isRefreshing = true;
      try {
        await Promise.all([loadSummary(), loadChart()]);
        updateLastUpdated();
      } finally {
        isRefreshing = false;
      }
    }

    document.getElementById('barBtn').addEventListener('click', () => setMode('bar'));
    document.getElementById('lineBtn').addEventListener('click', () => setMode('line'));
    refreshDashboard();
    setInterval(refreshDashboard, 3000);
  </script>
</body>
</html>
"""


def _build_changes_html():
    return """<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>每小时变化</title>
  <style>
    :root {
      --bg: #09111f;
      --panel: rgba(16, 24, 40, 0.78);
      --panel-border: rgba(148, 163, 184, 0.14);
      --text: #e5eefc;
      --muted: #9fb0c9;
      --primary: #60a5fa;
      --shadow: 0 20px 50px rgba(0, 0, 0, 0.28);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: var(--text);
      font-family: \"Segoe UI\", \"Microsoft YaHei\", Arial, sans-serif;
      background:
        radial-gradient(circle at top left, rgba(59,130,246,0.20), transparent 28%),
        radial-gradient(circle at top right, rgba(52,211,153,0.14), transparent 24%),
        linear-gradient(180deg, #0a1221 0%, #08101d 100%);
      min-height: 100vh;
    }
    .wrap { max-width: 1180px; margin: 0 auto; padding: 28px; }
    .hero {
      display: flex; justify-content: space-between; gap: 16px; align-items: center;
      margin-bottom: 20px; padding: 24px 26px;
      border: 1px solid var(--panel-border); border-radius: 24px;
      background: linear-gradient(135deg, rgba(17,24,39,0.88), rgba(15,23,42,0.72));
      box-shadow: var(--shadow); backdrop-filter: blur(16px);
    }
    .hero h1 { margin: 0 0 6px; font-size: 28px; }
    .hero p { margin: 0; color: var(--muted); }
    .hero a {
      color: var(--text); background: rgba(51,65,85,0.68); border: 1px solid rgba(148,163,184,0.16);
      padding: 10px 15px; border-radius: 999px; text-decoration: none; transition: all .18s ease;
    }
    .hero a:hover { transform: translateY(-1px); background: rgba(71,85,105,0.8); }
    .card {
      background: var(--panel); border: 1px solid var(--panel-border); border-radius: 24px;
      padding: 24px; box-shadow: var(--shadow); backdrop-filter: blur(14px);
    }
    .header-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 16px; }
    .header-row h2 { margin: 0; font-size: 22px; }
    .muted { color: var(--muted); }
    .table-wrap {
      overflow: auto; border-radius: 18px; border: 1px solid rgba(148,163,184,0.12);
      background: rgba(8,15,28,0.65);
    }
    table { width: 100%; border-collapse: collapse; min-width: 760px; }
    thead th {
      position: sticky; top: 0; background: rgba(15,23,42,0.95); color: #cfe0ff; font-weight: 600;
    }
    th, td { padding: 14px 14px; border-bottom: 1px solid rgba(148,163,184,0.10); text-align: right; }
    th:first-child, td:first-child { text-align: left; }
    tbody tr:nth-child(even) { background: rgba(15,23,42,0.38); }
    tbody tr:hover { background: rgba(30,41,59,0.55); }
    .pill {
      display: inline-block; padding: 6px 10px; border-radius: 999px;
      background: rgba(96,165,250,0.12); color: #bfdbfe; border: 1px solid rgba(96,165,250,0.18);
      font-size: 12px;
    }
    @media (max-width: 900px) {
      .hero { flex-direction: column; align-items: flex-start; }
    }
  </style>
</head>
<body>
  <div class=\"wrap\">
    <section class=\"hero\">
      <div>
        <h1>每小时变化</h1>
        <p>自动刷新 credit、credit_all、sp、sp_use 变化数据</p>
      </div>
      <a href=\"/\">返回首页</a>
    </section>

    <section class=\"card\">
      <div class=\"header-row\">
        <h2>小时明细</h2>
        <span id=\"lastUpdated\" class=\"pill\">最后更新时间：--</span>
      </div>
      <div class=\"table-wrap\">
        <table>
          <thead>
            <tr>
              <th>小时</th>
              <th>credit</th>
              <th>credit_all</th>
              <th>sp</th>
              <th>sp_use</th>
            </tr>
          </thead>
          <tbody id=\"rows\"></tbody>
        </table>
      </div>
    </section>
  </div>
  <script>
    let isRefreshing = false;
    const animatedValues = new Map();

    function formatNumber(value) {
      return new Intl.NumberFormat('zh-CN').format(Number(value || 0));
    }

    function animateCell(cellId, toValue, duration = 500) {
      const element = document.getElementById(cellId);
      if (!element) {
        return;
      }
      const fromValue = Number(animatedValues.get(cellId) || 0);
      const targetValue = Number(toValue || 0);
      const start = performance.now();

      function frame(now) {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const value = Math.round(fromValue + (targetValue - fromValue) * eased);
        element.textContent = formatNumber(value);
        if (progress < 1) {
          requestAnimationFrame(frame);
        }
      }

      animatedValues.set(cellId, targetValue);
      requestAnimationFrame(frame);
    }

    function updateLastUpdated() {
      const now = new Date();
      document.getElementById('lastUpdated').textContent = `最后更新时间：${now.toLocaleTimeString('zh-CN')}`;
    }

    async function loadRows() {
      const response = await fetch('/api/hourly-changes?fields=credit,credit_all,sp,sp_use');
      const data = await response.json();
      const tbody = document.getElementById('rows');
      const rows = data.rows || [];
      const hasData = rows.some(row => Number(row.credit || 0) > 0 || Number(row.credit_all || 0) > 0 || Number(row.sp || 0) > 0 || Number(row.sp_use || 0) > 0);
      if (!hasData) {
        tbody.innerHTML = '<tr><td colspan="5" class="muted">暂无数据，等待新日志...</td></tr>';
        return;
      }
      tbody.innerHTML = rows.map((row, index) => `
        <tr>
          <td>${row.hour}</td>
          <td id="credit-${index}">0</td>
          <td id="credit-all-${index}">0</td>
          <td id="sp-${index}">0</td>
          <td id="sp-use-${index}">0</td>
        </tr>
      `).join('');
      rows.forEach((row, index) => {
        animateCell(`credit-${index}`, row.credit);
        animateCell(`credit-all-${index}`, row.credit_all);
        animateCell(`sp-${index}`, row.sp);
        animateCell(`sp-use-${index}`, row.sp_use);
      });
    }

    async function refreshRows() {
      if (isRefreshing) {
        return;
      }
      isRefreshing = true;
      try {
        await loadRows();
        updateLastUpdated();
      } finally {
        isRefreshing = false;
      }
    }

    refreshRows();
    setInterval(refreshRows, 5000);
  </script>
</body>
</html>
"""
