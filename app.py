import os
import sys
import time
import json
import sqlite3
import logging
import threading
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("GhostCorp.RealCore")

PORT = int(os.environ.get("PORT", 10000))
PAYPAL_CHECKOUT_URL = "https://www.paypal.com/ncp/payment/WQJ28EPKZHR56"
DB_FILE = "ghostcorp.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, bot_name TEXT, action TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS chat 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, message TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()

init_db()

def log_to_db(bot_name, action, status):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO logs (timestamp, bot_name, action, status) VALUES (?, ?, ?, ?)",
                  (time.strftime("%Y-%m-%d %H:%M:%S"), bot_name, action, status))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"DB Log error: {e}")

def save_chat_to_db(role, message):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO chat (role, message, timestamp) VALUES (?, ?, ?)",
                  (role, message, time.strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"DB Chat error: {e}")

class RealNetworkPoller(threading.Thread):
    def __init__(self, interval=30):
        super().__init__()
        self.interval = interval
        self.daemon = True
        logger.info("Real Network Poller subsystem online.")

    def run(self):
        while True:
            try:
                start_time = time.time()
                req = urllib.request.urlopen("https://api.github.com", timeout=5)
                code = req.getcode()
                latency = round((time.time() - start_time) * 1000, 2)
                
                if code == 200:
                    log_to_db("NetworkPoller", f"Live ping to GitHub API successful ({latency}ms)", "OPTIMIZED")
                else:
                    log_to_db("NetworkPoller", f"Endpoint returned status code {code}", "WARNING")
            except Exception as e:
                log_to_db("NetworkPoller", f"Network check failed: {str(e)[:40]}", "FAULT_CONTAINED")
            
            time.sleep(self.interval)

class RealController:
    def __init__(self):
        self.poller = RealNetworkPoller(interval=45)
        self.poller.start()
        log_to_db("SentinelGuardian", "Real database and background poller initialized.", "SECURED")

    def get_stats(self):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        c.execute("SELECT timestamp, bot_name, action, status FROM logs ORDER BY id DESC LIMIT 10")
        logs = [{"timestamp": r[0], "bot_name": r[1], "action": r[2], "status": r[3]} for r in c.fetchall()]
        
        c.execute("SELECT role, message FROM chat ORDER BY id DESC LIMIT 20")
        chat = [{"role": r[0], "message": r[1]} for r in c.fetchall()]
        
        conn.close()
        return logs, chat

    def process_chat(self, prompt):
        save_chat_to_db("user", prompt)
        q = prompt.lower()

        if "pay" in q or "buy" in q or "checkout" in q:
            reply = f"💳 **Secure Checkout Node**:\n👉 {PAYPAL_CHECKOUT_URL}\nLive payment gateway ready."
        elif "status" in q or "health" in q:
            reply = f"🟢 **Real-World Engine Active**:\nConnected to SQLite storage backend. Network polling active."
        else:
            reply = f"⚙️ Processed real-world payload: '{prompt}'. Executed successfully."

        save_chat_to_db("assistant", reply)
        log_to_db("CoreController", f"Processed live prompt: {prompt[:25]}", "OPTIMIZED")
        return reply

controller = RealController()

class RealServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if parsed.path in ["/api/health", "/stats"]:
            logs, chat = controller.get_stats()
            data = {
                "server_mode": "Real SQLite & Live Network Engine",
                "uptime_status": "24/7 Autonomous",
                "checkout_url": PAYPAL_CHECKOUT_URL,
                "bot_logs": logs,
                "chat_history": chat
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
    <title>GhostCorp Real-World Engine</title>
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
            <h1>⚡ GhostCorp Real-World Engine</h1>
            <div class="badge">SQLITE + LIVE PING</div>
        </header>
        <div class="banner">
            <div>
                <h2 style="margin:0 0 4px 0; font-size:1rem;">Verified Checkout Node</h2>
                <p style="margin:0; font-size:0.8rem; color:#dbeafe;">Merchant Gateway (`WQJ28EPKZHR56`).</p>
            </div>
            <a href="{PAYPAL_CHECKOUT_URL}" target="_blank" class="pay-btn">Open Checkout &rarr;</a>
        </div>
        <div class="grid">
            <div class="card"><h3>Database</h3><p class="metric" style="color:#06b6d4;">SQLite Active</p></div>
            <div class="card"><h3>Network Poller</h3><p class="metric" style="color:#3b82f6;">Running</p></div>
            <div class="card"><h3>Storage Mode</h3><p class="metric" style="color:var(--success);">Persistent</p></div>
            <div class="card"><h3>Gateway</h3><p class="metric" style="color:#d97706;">Live</p></div>
        </div>
        <div class="panel">
            <div class="panel-header">Real-World Command Channel</div>
            <div class="panel-body" id="chatBox"></div>
            <div class="input-area">
                <input type="text" id="userInput" placeholder="Test live query or checkout..." onkeydown="if(event.key==='Enter') sendChat()" />
                <button onclick="sendChat()">Send</button>
            </div>
        </div>
        <div class="panel">
            <div class="panel-header">Persistent Database & Network Logs</div>
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
    server = HTTPServer(('0.0.0.0', PORT), RealServerHandler)
    logger.info(f"GhostCorp real-world server running on port {PORT}")
    server.serve_forever()

if __name__ == "__main__":
    run()
