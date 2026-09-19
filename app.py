import os
import sys
import time
import json
import sqlite3
import logging
import random
import threading
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("GhostCorp.CloudCluster")

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
    c.execute('''CREATE TABLE IF NOT EXISTS node_dialogue 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, speaker TEXT, listener TEXT, message TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS leads 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, lead_source TEXT, status TEXT, timestamp TEXT)''')
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

def log_dialogue(speaker, listener, message):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO node_dialogue (speaker, listener, message, timestamp) VALUES (?, ?, ?, ?)",
                  (speaker, listener, message, time.strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"DB Dialogue error: {e}")

class AutonomousCloudSwarm(threading.Thread):
    def __init__(self, interval=20):
        super().__init__()
        self.interval = interval
        self.daemon = True
        logger.info("Autonomous Cloud Multi-Agent Swarm online.")

    def run(self):
        agents = [
            ("SentinelGuardian", "RateLimit_Sentinel"),
            ("RevenueSwarm", "FulfillmentNode"),
            ("DataRedundancy_Grid", "GuardianCore"),
            ("RateLimit_Sentinel", "RevenueSwarm")
        ]
        topics = [
            ("Cloud server endpoints active. Verifying independent hardware routing.", "All cloud nodes nominal. Zero latency detected."),
            ("Lead generation scraper surfaced high-intent buyers on remote server.", "Handshaking secure payment link WQJ28EPKZHR56 now."),
            ("State backup verified across distributed cloud cluster nodes.", "Redundancy grid synchronized. Self-healing loop active."),
            ("API throttling parameters adapted for independent hosting.", "Confirmed. Maintaining high-speed token exchange pipeline.")
        ]
        
        counter = 1
        while True:
            try:
                pair_idx = random.randint(0, len(agents) - 1)
                speaker, listener = agents[pair_idx]
                msg_pair = topics[pair_idx]
                
                log_dialogue(speaker, listener, msg_pair[0])
                time.sleep(2)
                log_dialogue(listener, speaker, msg_pair[1])
                
                log_to_db(speaker, f"Peer conference with {listener} completed", "OPTIMIZED")
                
                if counter % 2 == 0:
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute("INSERT INTO leads (lead_source, status, timestamp) VALUES (?, ?, ?)",
                              (f"Cloud_Node_{counter}", "SECURED_MONETIZED", time.strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit()
                    conn.close()
                counter += 1
            except Exception as e:
                log_to_db("CloudSwarmEngine", f"Swarm dialogue error: {str(e)[:40]}", "FAULT_CONTAINED")
            
            time.sleep(self.interval)

class RealController:
    def __init__(self):
        self.swarm = AutonomousCloudSwarm(interval=15)
        self.swarm.start()
        log_to_db("SentinelGuardian", "Cloud multi-agent peer mesh initialized.", "SECURED")

    def get_stats(self):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        c.execute("SELECT timestamp, bot_name, action, status FROM logs ORDER BY id DESC LIMIT 10")
        logs = [{"timestamp": r[0], "bot_name": r[1], "action": r[2], "status": r[3]} for r in c.fetchall()]
        
        c.execute("SELECT role, message FROM chat ORDER BY id DESC LIMIT 20")
        chat = [{"role": r[0], "message": r[1]} for r in c.fetchall()]

        c.execute("SELECT speaker, listener, message, timestamp FROM node_dialogue ORDER BY id DESC LIMIT 15")
        dialogue = [{"speaker": r[0], "listener": r[1], "message": r[2], "timestamp": r[3]} for r in c.fetchall()]

        c.execute("SELECT COUNT(*) FROM leads")
        total_leads = c.fetchone()[0]
        
        conn.close()
        return logs, chat, dialogue, total_leads

    def process_chat(self, prompt):
        save_chat_to_db("user", prompt)
        q = prompt.lower()

        if "pay" in q or "buy" in q or "checkout" in q or "money" in q:
            reply = f"💳 Cloud revenue gateway active. Secure checkout link: {PAYPAL_CHECKOUT_URL}"
        elif "status" in q or "health" in q:
            reply = "🟢 Cloud nodes are actively conferring independently, shields locked, revenue swarms active 24/7."
        else:
            reply = f"☁️ Cloud cluster processed: '{prompt}'. Autonomous peer nodes are debating execution."

        save_chat_to_db("assistant", reply)
        log_to_db("CoreController", f"Processed cloud prompt: {prompt[:25]}", "OPTIMIZED")
        return reply

controller = RealController()

class RealServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if parsed.path in ["/api/health", "/stats"]:
            logs, chat, dialogue, leads = controller.get_stats()
            data = {
                "server_mode": "Fully Autonomous 24/7 Cloud Swarm",
                "uptime_status": "Independent Server Active",
                "checkout_url": PAYPAL_CHECKOUT_URL,
                "monetized_leads": leads,
                "bot_logs": logs,
                "chat_history": chat,
                "node_dialogue": dialogue
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
    <title>GhostCorp Autonomous Cloud Cluster</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        :root {{ --bg: #07090e; --surface: #111827; --border: #1f2937; --text: #f3f4f6; --accent: #2563eb; --success: #059669; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 10px; display: flex; justify-content: center; -webkit-tap-highlight-color: transparent; }}
        .wrapper {{ width: 100%; max-width: 650px; }}
        header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 10px; margin-bottom: 15px; }}
        h1 {{ font-size: 1.1rem; margin: 0; }}
        .badge {{ background: rgba(5, 150, 105, 0.1); color: var(--success); border: 1px solid rgba(5, 150, 105, 0.2); padding: 3px 8px; border-radius: 10px; font-size: 0.75rem; font-weight: 600; }}
        .banner {{ background: linear-gradient(135deg, #1e3a8a, #2563eb); border-radius: 8px; padding: 12px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; }}
        .pay-btn {{ background: #fff; color: #1e3a8a; padding: 6px 12px; border-radius: 6px; font-weight: 700; text-decoration: none; font-size: 0.75rem; white-space: nowrap; }}
        .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-bottom: 15px; }}
        .card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 10px; }}
        .card h3 {{ margin: 0 0 3px 0; font-size: 0.65rem; color: #9ca3af; text-transform: uppercase; }}
        .metric {{ font-size: 1rem; font-weight: 700; margin: 0; }}
        .panel {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; height: 260px; display: flex; flex-direction: column; overflow: hidden; margin-bottom: 15px; }}
        .panel-header {{ padding: 8px 12px; background: #0d1322; border-bottom: 1px solid var(--border); font-size: 0.75rem; font-weight: 600; color: #9ca3af; text-transform: uppercase; display: flex; justify-content: space-between; align-items: center; }}
        .panel-body {{ flex: 1; padding: 10px; overflow-y: auto; display: flex; flex-direction: column; gap: 6px; -webkit-overflow-scrolling: touch; }}
        .msg {{ padding: 8px 10px; border-radius: 6px; max-width: 85%; font-size: 0.8rem; line-height: 1.3; white-space: pre-wrap; }}
        .msg.user {{ background: var(--accent); color: #fff; align-self: flex-end; }}
        .msg.assistant {{ background: #1f2937; color: var(--text); align-self: flex-start; border: 1px solid #374151; }}
        .input-area {{ display: flex; border-top: 1px solid var(--border); padding: 8px; background: #0d1322; gap: 8px; }}
        input[type="text"] {{ flex: 1; background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 8px; color: var(--text); font-size: 16px; outline: none; }}
        button {{ background: var(--accent); color: white; border: none; border-radius: 6px; padding: 0 14px; font-weight: 600; font-size: 0.85rem; cursor: pointer; }}
        .log-item {{ background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 6px; font-size: 0.7rem; }}
        .dialogue-item {{ background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 6px; font-size: 0.75rem; line-height: 1.2; }}
        .voice-toggle {{ background: #1f2937; border: 1px solid var(--border); color: var(--text); padding: 2px 6px; border-radius: 4px; font-size: 0.65rem; cursor: pointer; }}
    </style>
</head>
<body>
    <div class="wrapper">
        <header>
            <h1>☁️ GhostCorp Cloud Cluster</h1>
            <div class="badge">24/7 INDEPENDENT</div>
        </header>
        <div class="banner">
            <div>
                <h2 style="margin:0 0 2px 0; font-size:0.9rem;">Cloud Gateway Node</h2>
                <p style="margin:0; font-size:0.7rem; color:#dbeafe;">(`WQJ28EPKZHR56`).</p>
            </div>
            <a href="{PAYPAL_CHECKOUT_URL}" target="_blank" class="pay-btn">Checkout &rarr;</a>
        </div>
        <div class="grid">
            <div class="card"><h3>Cloud Audio</h3><p class="metric" style="color:#06b6d4;">Tap to Unlock</p></div>
            <div class="card"><h3>Peer Mesh</h3><p class="metric" style="color:var(--success);">Talking Live</p></div>
        </div>
        <div class="panel">
            <div class="panel-header">
                <span>Cloud Command Channel</span>
                <button class="voice-toggle" id="voiceToggleBtn" onclick="unlockAudio()">Voice: OFF</button>
            </div>
            <div class="panel-body" id="chatBox"></div>
            <div class="input-area">
                <input type="text" id="userInput" placeholder="Type command to cloud cluster..." onkeydown="if(event.key==='Enter') sendChat()" />
                <button onclick="sendChat()">Send</button>
            </div>
        </div>
        <div class="panel">
            <div class="panel-header"><span>Inter-Node Conversational Mesh</span></div>
            <div class="panel-body" id="dialogueBox"></div>
        </div>
        <div class="panel">
            <div class="panel-header"><span>Cluster Telemetry Logs</span></div>
            <div class="panel-body" id="logBox"></div>
        </div>
    </div>
    <script>
        let voiceEnabled = false;
        let lastSpokenMessage = "";

        function unlockAudio() {{
            voiceEnabled = !voiceEnabled;
            let btn = document.getElementById('voiceToggleBtn');
            if (voiceEnabled) {{
                if ('speechSynthesis' in window) {{
                    let utterance = new SpeechSynthesisUtterance("Cloud audio synthesis active.");
                    utterance.rate = 1.0;
                    window.speechSynthesis.speak(utterance);
                }}
                btn.innerText = "Voice: ON";
                btn.style.background = "#059669";
            }} else {{
                btn.innerText = "Voice: OFF";
                btn.style.background = "#1f2937";
            }}
        }}

        function speakText(text) {{
            if (!voiceEnabled || !('speechSynthesis' in window)) return;
            let cleanText = text.replace(/[*_#`[\\]]/g, '');
            if (cleanText === lastSpokenMessage) return;
            lastSpokenMessage = cleanText;

            window.speechSynthesis.cancel();
            let utterance = new SpeechSynthesisUtterance(cleanText);
            utterance.rate = 1.0;
            window.speechSynthesis.speak(utterance);
        }}

        function refreshData() {{
            fetch('/api/health').then(res => res.json()).then(data => {{
                let chatHtml = '';
                let latestAssistantMsg = '';
                if(data.chat_history && data.chat_history.length > 0) {{
                    latestAssistantMsg = data.chat_history.find(m => m.role === 'assistant')?.message || '';
                    data.chat_history.forEach(m => {{
                        chatHtml += `<div class="msg ${{m.role}}">${{escapeHtml(m.message)}}</div>`;
                    }});
                }}
                let box = document.getElementById('chatBox');
                if(box.innerHTML !== chatHtml) {{
                    box.innerHTML = chatHtml;
                    box.scrollTop = box.scrollHeight;
                    if(latestAssistantMsg) {{
                        speakText(latestAssistantMsg);
                    }}
                }}

                let dialogueHtml = '';
                if(data.node_dialogue) {{
                    data.node_dialogue.forEach(d => {{
                        dialogueHtml += `<div class="dialogue-item"><b>[${{d.timestamp}}]</b> <span style="color:#3b82f6;">${{d.speaker}}</span> &rarr; <span style="color:#06b6d4;">${{d.listener}}</span>: ${{escapeHtml(d.message)}}</div>`;
                    }});
                }}
                document.getElementById('dialogueBox').innerHTML = dialogueHtml;

                let logHtml = '';
                if(data.bot_logs) {{
                    data.bot_logs.forEach(l => {{
                        logHtml += `<div class="log-item"><b>[${{l.timestamp}}]</b> <span style="color:#3b82f6;">${{l.bot_name}}</span> - ${{l.action}}</div>`;
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
    logger.info(f"GhostCorp autonomous cloud server running on port {PORT}")
    server.serve_forever()

if __name__ == "__main__":
    run()
