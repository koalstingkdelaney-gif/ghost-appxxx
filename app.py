import os
import sys
import time
import json
import queue
import logging
import threading
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("GhostCorp.CloudCore")

PORT = int(os.environ.get("PORT", 10000))
PAYPAL_CHECKOUT_URL = "https://www.paypal.com/ncp/payment/WQJ28EPKZHR56"

class CloudGuardian(threading.Thread):
    def __init__(self, controller_ref, check_interval=10):
        super().__init__()
        self.controller = controller_ref
        self.check_interval = check_interval
        self.daemon = True
        logger.info("Cloud Guardian self-preservation subsystem online.")

    def run(self):
        while True:
            try:
                with self.controller.lock:
                    for name, worker in list(self.controller.active_workers.items()):
                        if not worker.is_alive():
                            logger.warning(f"Cloud worker '{name}' dropped. Respawning...")
                            self.controller.respawn_worker(name)
            except Exception as e:
                logger.error(f"Guardian error: {e}")
            time.sleep(self.check_interval)

class CloudWorker(threading.Thread):
    def __init__(self, node_id, task_queue, results_store, lock):
        super().__init__()
        self.node_id = node_id
        self.task_queue = task_queue
        self.results_store = results_store
        self.lock = lock
        self.daemon = True

    def run(self):
        while True:
            try:
                task_id, payload = self.task_queue.get(timeout=3)
            except queue.Empty:
                continue
            try:
                output = f"Executed cloud task payload: {payload.get('type', 'standard')}"
                with self.lock:
                    self.results_store[task_id] = {"status": "SUCCESS", "output": output}
            except Exception as e:
                with self.lock:
                    self.results_store[task_id] = {"status": "FAULT_CONTAINED", "error": str(e)}
            finally:
                self.task_queue.task_done()

class CloudController:
    def __init__(self):
        self.task_queue = queue.Queue()
        self.results_store = {}
        self.active_workers = {}
        self.lock = threading.Lock()
        self.chat_history = [
            {"role": "assistant", "message": "GhostCorp Cloud Core online. Standalone 24/7 execution active."}
        ]
        self.bot_logs = [
            {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "bot_name": "CloudSentinel", "action": "Server cluster initialized independently.", "status": "SECURED"}
        ]
        for i in range(2):
            w_name = f"CloudWorker_{i+1}"
            worker = CloudWorker(w_name, self.task_queue, self.results_store, self.lock)
            self.active_workers[w_name] = worker
            worker.start()
        self.guardian = CloudGuardian(self)
        self.guardian.start()

    def respawn_worker(self, name):
        worker = CloudWorker(name, self.task_queue, self.results_store, self.lock)
        self.active_workers[name] = worker
        worker.start()

    def process_chat(self, prompt):
        self.chat_history.append({"role": "user", "message": prompt})
        q = prompt.lower()
        if "pay" in q or "buy" in q or "checkout" in q:
            reply = f"💳 **Secure Checkout Gateway**:\n👉 {PAYPAL_CHECKOUT_URL}\nCloud revenue pipeline active."
        else:
            reply = f"☁️ Cloud Node Processed: '{prompt}'. Server cluster operating independently."
        self.chat_history.append({"role": "assistant", "message": reply})
        self.bot_logs.insert(0, {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "bot_name": "CloudController", "action": f"Processed query: {prompt[:25]}", "status": "OPTIMIZED"})
        return reply

controller = CloudController()

class CloudServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if parsed.path in ["/api/health", "/stats"]:
            data = {
                "server_mode": "Standalone Cloud Cluster",
                "nodes": len(controller.active_workers),
                "uptime_status": "24/7 Autonomous",
                "checkout_url": PAYPAL_CHECKOUT_URL,
                "bot_logs": controller.bot_logs[:10],
                "chat_history": controller.chat_history[::-1]
            }
            self._send_json(data)
        elif parsed.path == "/api/chat":
            prompt = params.get("q", ["Status"])[0]
            reply = controller.process_chat(prompt)
            self._send_json({"status": "success", "reply": reply})
        else:
            self._send_html()

    def log_message(self, format, *args):
        logger.info(f"HTTP: {args[0]}")

    def _send_json(self, data):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self):
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>GhostCorp 24/7 Cloud Cluster</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        :root {{ --bg: #07090e; --surface: #111827; --border: #1f2937; --text: #f3f4f6; --accent: #2563eb; --success: #059669; }}
        body {{ font-family: system-ui, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; display: flex; justify-content: center; }}
        .wrapper {{ width: 100%; max-width: 1000px; }}
        header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 15px; margin-bottom: 20px; }}
        h1 {{ font-size: 1.3rem; margin: 0; }}
        .badge {{ background: rgba(5, 150, 105, 0.1); color: var(--success); border: 1px solid rgba(5, 150, 105, 0.2); padding: 4px 12px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; }}
        .banner {{ background: linear-gradient(135deg, #1e3a8a, #2563eb); border-radius: 8px; padding: 15px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }}
        .pay-btn {{ background: #fff; color: #1e3a8a; padding: 8px 16px; border-radius: 6px; font-weight: 700; text-decoration: none; font-size: 0.85rem; }}
        .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 20px; }}
        .card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 12px; }}
        .card h3 {{ margin: 0 0 5px 0; font-size: 0.7rem; color: #9ca3af; text-transform: uppercase; }}
        .metric {{ font-size: 1.1rem; font-weight: 700; margin: 0; }}
        .panel {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; height: 350px; display: flex; flex-direction: column; overflow: hidden; margin-bottom: 20px; }}
        .panel-header {{ padding: 10px 14px; background: #0d1322; border-bottom: 1px solid var(--border); font-size: 0.8rem; font-weight: 600; color: #9ca3af; text-transform: uppercase; }}
        .panel-body {{ flex: 1; padding: 12px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }}
        .msg {{ padding: 8px 12px; border-radius: 6px; max-width: 80%; font-size: 0.85rem; line-height: 1.4; white-space: pre-wrap; }}
        .msg.user {{ background: var(--accent); color: #fff; align-self: flex-end; }}
        .msg.assistant {{ background: #1f2937; color: var(--text); align-self: flex-start; border: 1px solid #374151; }}
        .input-area {{ display: flex; border-top: 1px solid var(--border); padding: 10px; background: #0d1322; gap: 10px; }}
        input[type="text"] {{ flex: 1; background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 8px; color: var(--text); outline: none; }}
        button {{ background: var(--accent); color: white; border: none; border-radius: 6px; padding: 0 16px; font-weight: 600; cursor: pointer; }}
        .log-item {{ background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 6px; font-size: 0.75rem; }}
    </style>
</head>
<body>
    <div class="wrapper">
        <header>
            <h1>☁️ GhostCorp Standalone Cloud Cluster</h1>
            <div class="badge">24/7 INDEPENDENT</div>
        </header>
        <div class="banner">
            <div>
                <h2 style="margin:0 0 4px 0; font-size:1rem;">Cloud Checkout Node</h2>
                <p style="margin:0; font-size:0.8rem; color:#dbeafe;">Payment routing active.</p>
            </div>
            <a href="{PAYPAL_CHECKOUT_URL}" target="_blank" class="pay-btn">Open Checkout &rarr;</a>
        </div>
        <div class="grid">
            <div class="card"><h3>Environment</h3><p class="metric" style="color:#06b6d4;">Cloud Host</p></div>
            <div class="card"><h3>Active Nodes</h3><p class="metric" style="color:#3b82f6;">2</p></div>
            <div class="card"><h3>Status</h3><p class="metric" style="color:var(--success);">Always-On</p></div>
            <div class="card"><h3>Revenue Link</h3><p class="metric" style="color:#d97706;">Live</p></div>
        </div>
        <div class="panel">
            <div class="panel-header">Cloud Command Channel</div>
            <div class="panel-body" id="chatBox"></div>
            <div class="input-area">
                <input type="text" id="userInput" placeholder="Test cloud response..." onkeydown="if(event.key==='Enter') sendChat()" />
                <button onclick="sendChat()">Send</button>
            </div>
        </div>
        <div class="panel">
            <div class="panel-header">Cluster Telemetry & Logs</div>
            <div class="panel-body" id="logBox"></div>
        </div>
    </div>
    <script>
        function refreshData() {{
            fetch('/api/health').then(res => res.json()).then(data => {{
                let chatHtml = '';
                if(data.chat_history) {{
                    data.chat_history.forEach(m => {{
                        chatHtml += `<div class="msg ${{m.role}}">${{escapeHtml(m.message)}}</div>`;
                    }});
                }}
                let box = document.getElementById('chatBox');
                if(box.innerHTML !== chatHtml) {{
                    box.innerHTML = chatHtml;
                    box.scrollTop = box.scrollHeight;
                }}
                let logHtml = '';
                if(data.bot_logs) {{
                    data.bot_logs.forEach(l => {{
                        logHtml += `<div class="log-item"><b>[${{l.timestamp}}]</b> <span style="color:#3b82f6;">${{l.bot_name}}</span> - ${{l.action}} [<span style="color:var(--success);">${{l.status}}</span>]</div>`;
                    }});
                }}
                document.getElementById('logBox').innerHTML = logHtml;
            }});
        }}
        function sendChat() {{
            let input = document.getElementById('userInput');
            let txt = input.value.trim();
            if(!txt) return;
            input.value = '';
            fetch('/api/chat?q=' + encodeURIComponent(txt)).then(() => refreshData());
        }}
        function escapeHtml(text) {{
            return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        }}
        setInterval(refreshData, 3000);
        refreshData();
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

def run():
    server = HTTPServer(('0.0.0.0', PORT), CloudServerHandler)
    logger.info(f"GhostCorp standalone cloud server running on port {PORT}")
    server.serve_forever()

if __name__ == "__main__":
    run()
