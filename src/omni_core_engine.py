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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("OmniHiveTrueEngine")

PORT = int(os.environ.get("PORT", 8080))
DB_PATH = "omni_hive_true.db"
PAYPAL_CHECKOUT_URL = "https://www.paypal.com/ncp/payment/WQJ28EPKZHR56"

class OmniHiveTrueManager:
    def __init__(self):
        self._init_db()
        self.lock = threading.Lock()
        logger.info("Omni-Hive True-State Engine initialized.")

    def _init_db(self):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    key TEXT PRIMARY KEY,
                    value REAL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bot_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    bot_name TEXT,
                    action TEXT,
                    status TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    role TEXT,
                    message TEXT
                )
            """)
            # Zero out simulated placeholders for accurate real-time tracking
            cursor.execute("INSERT OR IGNORE INTO metrics (key, value) VALUES ('connected_servers', 0)")
            cursor.execute("INSERT OR IGNORE INTO metrics (key, value) VALUES ('active_nodes', 0)")
            cursor.execute("INSERT OR IGNORE INTO metrics (key, value) VALUES ('total_revenue_usd', 0.00)")
            cursor.execute("INSERT OR IGNORE INTO metrics (key, value) VALUES ('acquired_leads', 0)")
            conn.commit()

    def get_stat(self, key):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM metrics WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else 0.0

    def log_bot(self, bot_name, action, status):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with self.lock:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO bot_logs (timestamp, bot_name, action, status) VALUES (?, ?, ?, ?)",
                    (timestamp, bot_name, action, status)
                )
                conn.commit()

    def log_chat(self, role, message):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with self.lock:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO chat_history (timestamp, role, message) VALUES (?, ?, ?)",
                    (timestamp, role, message)
                )
                conn.commit()

    def process_chat(self, prompt):
        self.log_chat("user", prompt)
        q = prompt.lower()

        if "pay" in q or "buy" in q or "checkout" in q or "transaction" in q:
            reply = (f"💳 **Secure Checkout Gateway**:\n"
                     f"👉 {PAYPAL_CHECKOUT_URL}")
            self.log_bot("PaymentBot", "Provided live checkout link", "READY")
        else:
            reply = (f"🤖 Runtime Directive Processed: '{prompt}'.\n"
                     f"System operating on true runtime state. Checkout: {PAYPAL_CHECKOUT_URL}")

        self.log_chat("assistant", reply)
        return reply

    def get_dashboard_data(self):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp, bot_name, action, status FROM bot_logs ORDER BY id DESC LIMIT 15")
            logs = [{"timestamp": r[0], "bot_name": r[1], "action": r[2], "status": r[3]} for r in cursor.fetchall()]

            cursor.execute("SELECT timestamp, role, message FROM chat_history ORDER BY id DESC LIMIT 20")
            chats = [{"timestamp": r[0], "role": r[1], "message": r[2]} for r in cursor.fetchall()]

        return {
            "servers": int(self.get_stat("connected_servers")),
            "nodes": int(self.get_stat("active_nodes")),
            "total_revenue_usd": self.get_stat("total_revenue_usd"),
            "acquired_leads": int(self.get_stat("acquired_leads")),
            "checkout_url": PAYPAL_CHECKOUT_URL,
            "bot_logs": logs,
            "chat_history": chats[::-1]
        }

hive = OmniHiveTrueManager()

class TrueHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_path.query)

            if parsed_path.path == "/api/health" or parsed_path.path == "/stats":
                data = hive.get_dashboard_data()
                self._send_json_response(data)
            elif parsed_path.path == "/api/chat":
                prompt = query_params.get("q", ["Status"])[0]
                reply = hive.process_chat(prompt)
                self._send_json_response({"status": "success", "reply": reply})
            else:
                self._send_dashboard_response()
        except Exception as e:
            err_trace = traceback.format_exc()
            self._send_json_response({"status": "error", "message": str(e), "trace": err_trace}, status_code=500)

    def log_message(self, format, *args):
        logger.info(f"HTTP Access: {args[0]}")

    def _send_json_response(self, data, status_code=200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_dashboard_response(self):
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Omni-Hive True-State Telemetry</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        :root {{
            --bg: #07090e;
            --surface: #111827;
            --border: #1f2937;
            --text: #f3f4f6;
            --text-dim: #9ca3af;
            --accent: #2563eb;
            --success: #059669;
            --gold: #d97706;
            --cyan: #06b6d4;
        }}
        body {{ font-family: system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; display: flex; justify-content: center; }}
        .wrapper {{ width: 100%; max-width: 1050px; }}
        header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 15px; margin-bottom: 20px; }}
        h1 {{ font-size: 1.4rem; margin: 0; }}
        .badge {{ background: rgba(5, 150, 105, 0.1); color: var(--success); border: 1px solid rgba(5, 150, 105, 0.2); padding: 4px 12px; border-radius: 12px; font-size: 0.85rem; font-weight: 600; }}
        .checkout-banner {{ background: linear-gradient(135deg, #1e3a8a, #2563eb); border-radius: 10px; padding: 16px 20px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2); }}
        .checkout-banner h2 {{ margin: 0 0 4px 0; font-size: 1.1rem; }}
        .checkout-banner p {{ margin: 0; font-size: 0.85rem; color: #dbeafe; }}
        .pay-btn {{ background: #ffffff; color: #1e3a8a; padding: 10px 20px; border-radius: 6px; font-weight: 700; text-decoration: none; font-size: 0.9rem; transition: background 0.2s; }}
        .pay-btn:hover {{ background: #f8fafc; }}
        .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 20px; }}
        @media(max-width: 800px) {{ .grid {{ grid-template-columns: repeat(2, 1fr); }} }}
        .card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 12px; }}
        .card h3 {{ margin: 0 0 6px 0; font-size: 0.7rem; text-transform: uppercase; color: var(--text-dim); letter-spacing: 0.05em; }}
        .metric {{ font-size: 1.2rem; font-weight: 700; margin: 0; }}
        .main-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        @media(max-width: 800px) {{ .main-grid {{ grid-template-columns: 1fr; }} }}
        .panel {{ background: var(--surface); border: 1px solid var(--border); border-radius: 10px; display: flex; flex-direction: column; height: 400px; overflow: hidden; }}
        .panel-header {{ padding: 12px 16px; border-bottom: 1px solid var(--border); font-size: 0.85rem; font-weight: 600; text-transform: uppercase; color: var(--text-dim); background: #0d1322; }}
        .panel-body {{ flex: 1; padding: 12px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }}
        .msg {{ padding: 10px 14px; border-radius: 8px; max-width: 85%; font-size: 0.85rem; line-height: 1.4; white-space: pre-wrap; }}
        .msg.user {{ background: var(--accent); color: white; align-self: flex-end; }}
        .msg.assistant {{ background: #1f2937; color: var(--text); align-self: flex-start; border: 1px solid #374151; }}
        .chat-input-area {{ display: flex; border-top: 1px solid var(--border); padding: 10px; background: #0d1322; gap: 10px; }}
        input[type="text"] {{ flex: 1; background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 8px 12px; color: var(--text); font-size: 0.9rem; outline: none; }}
        input[type="text"]:focus {{ border-color: var(--accent); }}
        button {{ background: var(--accent); color: white; border: none; border-radius: 6px; padding: 0 16px; font-weight: 600; cursor: pointer; }}
        button:hover {{ background: #1d4ed8; }}
        .bot-log-item {{ background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 8px; font-size: 0.78rem; }}
    </style>
</head>
<body>
    <div class="wrapper">
        <header>
            <h1>⚡ Omni-Hive True-State Telemetry</h1>
            <div class="badge">LIVE RUNTIME ACTIVE</div>
        </header>

        <div class="checkout-banner">
            <div>
                <h2>Secure PayPal Checkout Portal</h2>
                <p>Transactions route directly through your verified business link.</p>
            </div>
            <a href="{PAYPAL_CHECKOUT_URL}" target="_blank" class="pay-btn">Proceed to Checkout &rarr;</a>
        </div>

        <div class="grid">
            <div class="card">
                <h3>Connected Servers</h3>
                <p class="metric" id="serverCount" style="color: var(--cyan);">0</p>
            </div>
            <div class="card">
                <h3>Active Nodes</h3>
                <p class="metric" id="nodeCount" style="color: #3b82f6;">0</p>
            </div>
            <div class="card">
                <h3>Total Revenue ($)</h3>
                <p class="metric" id="revCount" style="color: var(--success);">$0</p>
            </div>
            <div class="card">
                <h3>Acquired Leads</h3>
                <p class="metric" id="leadCount" style="color: var(--gold);">0</p>
            </div>
        </div>

        <div class="main-grid">
            <div class="panel">
                <div class="panel-header">Swarm Communication Channel</div>
                <div class="panel-body" id="chatBox">
                    <div class="msg assistant">Engine initialized on true runtime state. Ready for commands.</div>
                </div>
                <div class="chat-input-area">
                    <input type="text" id="userInput" placeholder="Send directive to swarm..." onkeydown="if(event.key==='Enter') sendChatMessage()" />
                    <button onclick="sendChatMessage()">Send</button>
                </div>
            </div>

            <div class="panel">
                <div class="panel-header">Real-Time Event Logs</div>
                <div class="panel-body" id="botLogBox">
                    <pre style="color: var(--text-dim); font-size: 0.75rem;">Listening for runtime telemetry...</pre>
                </div>
            </div>
        </div>
    </div>

    <script>
        function refreshTelemetry() {{
            fetch('/api/health')
                .then(res => res.json())
                .then(data => {{
                    document.getElementById('serverCount').innerText = data.servers;
                    document.getElementById('nodeCount').innerText = data.nodes;
                    document.getElementById('revCount').innerText = '$' + data.total_revenue_usd.toLocaleString(undefined, {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
                    document.getElementById('leadCount').innerText = data.acquired_leads;

                    let logHtml = '';
                    if(data.bot_logs && data.bot_logs.length > 0) {{
                        data.bot_logs.forEach(l => {{
                            logHtml += `<div class="bot-log-item"><b>[${{l.timestamp}}]</b> <span style="color: #0070ba;">${{l.bot_name}}</span><br>↳ ${{l.action}} [<span style="color: var(--success);">${{l.status}}</span>]</div>`;
                        }});
                    }} else {{
                        logHtml = `<pre style="color: var(--text-dim); font-size: 0.75rem;">No events logged yet.</pre>`;
                    }}
                    document.getElementById('botLogBox').innerHTML = logHtml;
                }})
                .catch(err => console.error("Sync error:", err));
        }}

        function loadChatHistory() {{
            fetch('/api/health')
                .then(res => res.json())
                .then(data => {{
                    let box = document.getElementById('chatBox');
                    let html = '';
                    if(data.chat_history && data.chat_history.length > 0) {{
                        data.chat_history.forEach(m => {{
                            html += `<div class="msg ${{m.role}}">${{escapeHtml(m.message)}}</div>`;
                        }});
                    }} else {{
                        html = `<div class="msg assistant">Ready.</div>`;
                    }}
                    box.innerHTML = html;
                    box.scrollTop = box.scrollHeight;
                }});
        }}

        function sendChatMessage() {{
            let input = document.getElementById('userInput');
            let txt = input.value.trim();
            if(!txt) return;

            let box = document.getElementById('chatBox');
            box.innerHTML += `<div class="msg user">${{escapeHtml(txt)}}</div>`;
            input.value = '';
            box.scrollTop = box.scrollHeight;

            fetch('/api/chat?q=' + encodeURIComponent(txt))
                .then(res => res.json())
                .then(data => {{
                    box.innerHTML += `<div class="msg assistant">${{escapeHtml(data.reply)}}</div>`;
                    box.scrollTop = box.scrollHeight;
                    refreshTelemetry();
                }});
        }}

        function escapeHtml(text) {{
            return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        }}

        setInterval(refreshTelemetry, 3000);
        refreshTelemetry();
        loadChatHistory();
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
    httpd = HTTPServer(server_address, TrueHandler)
    logger.info(f"Omni-Hive true-state server running on port {PORT}")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
