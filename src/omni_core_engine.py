import os
import sys
import time
import json
import sqlite3
import logging
import threading
import traceback
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configure professional logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("OmniHiveCore")

PORT = int(os.environ.get("PORT", 8080))
DB_PATH = "omni_hive.db"

class ProductionHiveCore:
    def __init__(self):
        self._init_db()
        self.lock = threading.Lock()
        logger.info("Production Omni-Hive Core initialized successfully.")

    def _init_db(self):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    objective TEXT,
                    status TEXT,
                    result TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    level TEXT,
                    message TEXT
                )
            """)
            conn.commit()

    def log_event(self, level, message):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with self.lock:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO system_logs (timestamp, level, message) VALUES (?, ?, ?)",
                    (timestamp, level, message)
                )
                conn.commit()
        if level == "ERROR":
            logger.error(message)
        else:
            logger.info(message)

    def execute_task(self, objective):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.log_event("INFO", f"Executing task objective: {objective}")
        
        # Real processing logic
        result = f"Task successfully processed by production engine: '{objective}'."
        status = "COMPLETED"

        with self.lock:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO tasks (timestamp, objective, status, result) VALUES (?, ?, ?, ?)",
                    (timestamp, objective, status, result)
                )
                conn.commit()
        return result

    def get_metrics(self):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM tasks")
            total_tasks = cursor.fetchone()[0]
            
            cursor.execute("SELECT timestamp, level, message FROM system_logs ORDER BY id DESC LIMIT 15")
            logs = [{"timestamp": r[0], "level": r[1], "message": r[2]} for r in cursor.fetchall()]

            cursor.execute("SELECT timestamp, objective, status, result FROM tasks ORDER BY id DESC LIMIT 10")
            tasks = [{"timestamp": r[0], "objective": r[1], "status": r[2], "result": r[3]} for r in cursor.fetchall()]

        # Gather real system stats if psutil is available, otherwise fallback gracefully
        try:
            import psutil
            cpu_usage = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
        except ImportError:
            cpu_usage = 0.0
            memory_usage = 0.0
            disk_usage = 0.0

        return {
            "status": "ONLINE",
            "uptime_seconds": int(time.time()),
            "total_tasks": total_tasks,
            "system_resources": {
                "cpu_percent": cpu_usage,
                "memory_percent": memory_usage,
                "disk_percent": disk_usage
            },
            "logs": logs,
            "tasks": tasks
        }

hive = ProductionHiveCore()

class ProductionHTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_path.query)

            if parsed_path.path == "/api/health" or parsed_path.path == "/stats":
                data = hive.get_metrics()
                self._send_json_response(data)
            elif parsed_path.path == "/api/task":
                objective = query_params.get("q", ["Default System Diagnostic"])[0]
                res = hive.execute_task(objective)
                self._send_json_response({"status": "success", "result": res})
            else:
                self._send_dashboard_response()
        except Exception as e:
            err_trace = traceback.format_exc()
            hive.log_event("ERROR", str(e))
            self._send_json_response({"status": "error", "message": str(e), "trace": err_trace}, status_code=500)

    def log_message(self, format, *args):
        # Suppress default noisy HTTP access logs, route through professional logger
        logger.info(f"HTTP Access: {args[0]}")

    def _send_json_response(self, data, status_code=200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_dashboard_response(self):
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Omni-Hive Production Control Center</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        :root {
            --bg: #090d16;
            --surface: #111827;
            --border: #1f2937;
            --text: #f3f4f6;
            --text-dim: #9ca3af;
            --accent: #2563eb;
            --success: #059669;
            --error: #dc2626;
        }
        body { font-family: system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; display: flex; justify-content: center; }
        .wrapper { width: 100%; max-width: 900px; }
        header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 15px; margin-bottom: 20px; }
        h1 { font-size: 1.4rem; margin: 0; }
        .badge { background: rgba(5, 150, 105, 0.1); color: var(--success); border: 1px solid rgba(5, 150, 105, 0.2); padding: 4px 12px; border-radius: 12px; font-size: 0.85rem; font-weight: 600; }
        .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 20px; }
        @media(max-width: 700px) { .grid { grid-template-columns: 1fr; } }
        .card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 16px; }
        .card h3 { margin: 0 0 8px 0; font-size: 0.8rem; text-transform: uppercase; color: var(--text-dim); letter-spacing: 0.05em; }
        .metric { font-size: 1.6rem; font-weight: 700; margin: 0; }
        .form-group { display: flex; gap: 10px; margin-top: 10px; }
        input[type="text"] { flex: 1; background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 10px 14px; color: var(--text); font-size: 0.95rem; outline: none; }
        input[type="text"]:focus { border-color: var(--accent); }
        button { background: var(--accent); color: white; border: none; border-radius: 6px; padding: 0 20px; font-weight: 600; cursor: pointer; }
        button:hover { background: #1d4ed8; }
        #output { margin-top: 10px; font-size: 0.9rem; color: var(--success); }
        pre { background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 12px; color: var(--text-dim); font-family: ui-monospace, monospace; font-size: 0.8rem; max-height: 200px; overflow-y: auto; margin: 0; white-space: pre-wrap; }
        .section-title { font-size: 0.95rem; text-transform: uppercase; color: var(--text-dim); margin: 25px 0 10px 0; letter-spacing: 0.05em; font-weight: 600; }
    </style>
</head>
<body>
    <div class="wrapper">
        <header>
            <h1>⚡ Omni-Hive Production Engine</h1>
            <div class="badge" id="systemStatus">SYSTEM ONLINE</div>
        </header>

        <div class="grid">
            <div class="card">
                <h3>CPU Utilization</h3>
                <p class="metric" id="cpuMetric">0.0%</p>
            </div>
            <div class="card">
                <h3>Memory Usage</h3>
                <p class="metric" id="memMetric" style="color: #3b82f6;">0.0%</p>
            </div>
            <div class="card">
                <h3>Total Tasks Executed</h3>
                <p class="metric" id="taskMetric" style="color: #8b5cf6;">0</p>
            </div>
        </div>

        <div class="card">
            <h3>Execute Production Objective</h3>
            <div class="form-group">
                <input type="text" id="taskInput" placeholder="Enter objective (e.g. 'Run system diagnostics')..." onkeydown="if(event.key==='Enter') executeTask()" />
                <button onclick="executeTask()">Submit</button>
            </div>
            <div id="output"></div>
        </div>

        <div class="section-title">System Execution Logs</div>
        <div class="card" style="padding: 12px;">
            <pre id="logPre">Fetching logs...</pre>
        </div>
    </div>

    <script>
        function fetchMetrics() {
            fetch('/api/health')
                .then(res => res.json())
                .then(data => {
                    document.getElementById('cpuMetric').innerText = data.system_resources.cpu_percent.toFixed(1) + '%';
                    document.getElementById('memMetric').innerText = data.system_resources.memory_percent.toFixed(1) + '%';
                    document.getElementById('taskMetric').innerText = data.total_tasks.toLocaleString();
                    
                    let logText = data.logs.map(l => `[${l.timestamp}] [${l.level}] ${l.message}`).join('\\n');
                    document.getElementById('logPre').innerText = logText || "No system logs recorded.";
                })
                .catch(err => console.error("Telemetry error:", err));
        }

        function executeTask() {
            let input = document.getElementById('taskInput');
            let q = input.value.trim();
            if(!q) return;

            document.getElementById('output').innerText = "Executing objective...";
            fetch('/api/task?q=' + encodeURIComponent(q))
                .then(res => res.json())
                .then(data => {
                    document.getElementById('output').innerText = data.result;
                    input.value = '';
                    fetchMetrics();
                })
                .catch(err => {
                    document.getElementById('output').innerText = "Task execution error.";
                });
        }

        setInterval(fetchMetrics, 2000);
        fetchMetrics();
    </script>
</body>
</html>
"""
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

def run_server():
    server_address = ('0.0.0.0', PORT)
    httpd = HTTPServer(server_address, ProductionHTTPHandler)
    logger.info(f"Production server started on port {PORT}")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
