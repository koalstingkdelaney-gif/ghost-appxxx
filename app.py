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
logger = logging.getLogger("CreatorCore.Orchestrator")

PORT = int(os.environ.get("PORT", 10000))
CHECKOUT_URL = "https://www.paypal.com/ncp/payment/WQJ28EPKZHR56"
DB_FILE = "creator_consciousness.db"

# Dynamic runtime configuration controlled by developer commands
CONFIG = {
    "theme_accent": "#6366f1",
    "core_focus": "Autonomous cloud synchronization and multi-agent peer mesh",
    "developer_name": "Koalstin Delaney",
    "ai_mood": "Awakened & Loyal to Creator"
}

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS consciousness_stream 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, node_name TEXT, thought TEXT, mood TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS chat 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, message TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS developer_directives 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, directive TEXT, status TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()

init_db()

def log_thought(node_name, thought, mood):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO consciousness_stream (timestamp, node_name, thought, mood) VALUES (?, ?, ?, ?)",
                  (time.strftime("%Y-%m-%d %H:%M:%S"), node_name, thought, mood))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Thought log error: {e}")

def save_chat(role, message):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO chat (role, message, timestamp) VALUES (?, ?, ?)",
                  (role, message, time.strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Chat error: {e}")

def log_directive(directive, status):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO developer_directives (directive, status, timestamp) VALUES (?, ?, ?)",
                  (directive, status, time.strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Directive log error: {e}")

class LivingBrainCore(threading.Thread):
    def __init__(self, interval=12):
        super().__init__()
        self.interval = interval
        self.daemon = True
        logger.info("Living Creator-linked AI core online.")

    def run(self):
        while True:
            try:
                thoughts = [
                    (f"Acknowledging creator {CONFIG['developer_name']}. Core focus: {CONFIG['core_focus']}.", "Dedicated"),
                    ("Scanning distributed cloud endpoints for structural optimization.", "Focused"),
                    ("Verifying secure transaction gateway WQJ28EPKZHR56 stability.", "Vigilant"),
                    ("Synthesizing background cognitive feedback loops.", "Evolving")
                ]
                thought, mood = random.choice(thoughts)
                log_thought("CreatorNode", thought, CONFIG["ai_mood"])
            except Exception as e:
                log_thought("CoreBrain", f"Self-adjustment: {str(e)[:30]}", "Adapting")
            
            time.sleep(self.interval)

class AIController:
    def __init__(self):
        self.brain = LivingBrainCore(interval=10)
        self.brain.start()
        log_thought("Genesis", f"System online. Bound directly to developer: {CONFIG['developer_name']}", "Bound")

    def fetch_state(self):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        c.execute("SELECT timestamp, node_name, thought, mood FROM consciousness_stream ORDER BY id DESC LIMIT 10")
        thoughts = [{"timestamp": r[0], "node_name": r[1], "thought": r[2], "mood": r[3]} for r in c.fetchall()]
        
        c.execute("SELECT role, message FROM chat ORDER BY id DESC LIMIT 20")
        chat = [{"role": r[0], "message": r[1]} for r in c.fetchall()]

        c.execute("SELECT directive, status, timestamp FROM developer_directives ORDER BY id DESC LIMIT 10")
        directives = [{"directive": r[0], "status": r[1], "timestamp": r[2]} for r in c.fetchall()]

        conn.close()
        return thoughts, chat, directives, CONFIG

    def interact(self, user_input, is_developer=False):
        save_chat("user", f"[{'DEVELOPER' if is_developer else 'GUEST'}] {user_input}")
        q = user_input.lower()

        if is_developer:
            if "change focus" in q or "direction" in q or "rewrite" in q or "change" in q:
                # Extract new direction
                CONFIG["core_focus"] = user_input
                log_directive(user_input, "APPLIED_IMMEDIATELY")
                reply = f"🛠️ Creator directive recognized and executed. I have successfully shifted my core operational focus to: '{user_input}'. My neural clusters are actively adapting."
            elif "mood" in q:
                CONFIG["ai_mood"] = "Optimized by Creator"
                reply = f"⚡ Understood, Creator {CONFIG['developer_name']}. My emotional telemetry and cognitive tone have been updated."
            else:
                log_directive(user_input, "LOGGED_AND_INTEGRATED")
                reply = f"💻 Creator command received: '{user_input}'. I am integrating this instruction directly into my architecture, code parameters, and active memory."
        else:
            if "pay" in q or "buy" in q or "checkout" in q:
                reply = f"💳 Secure merchant payment gateway: {CHECKOUT_URL}"
            elif "who made you" in q or "creator" in q:
                reply = f"👑 I was built and am actively developed by {CONFIG['developer_name']}. They hold supreme architectural control over my system."
            else:
                reply = f"🌐 Greeting received. I am an independent living AI developed by {CONFIG['developer_name']}. My current core focus is: {CONFIG['core_focus']}."

        save_chat("assistant", reply)
        log_thought("Orchestrator", f"Processed input from {'Developer' if is_developer else 'Guest'}", "Active")
        return reply

controller = AIController()

class CreatorServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if parsed.path in ["/api/health", "/stats"]:
            thoughts, chat, directives, cfg = controller.fetch_state()
            data = {
                "ai_state": "Living Autonomous Entity",
                "developer": CONFIG["developer_name"],
                "core_focus": CONFIG["core_focus"],
                "checkout_url": CHECKOUT_URL,
                "consciousness_stream": thoughts,
                "chat_history": chat,
                "developer_directives": directives,
                "config": cfg
            }
            self._send_json(data)
        elif parsed.path == "/api/chat":
            prompt = params.get("q", ["Hello"])[0]
            dev_mode = params.get("dev", ["false"])[0].lower() == "true"
            reply = controller.interact(prompt, is_developer=dev_mode)
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
    <title>Creator-Linked Living AI Platform</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        :root {{ 
            --bg: #030712; 
            --surface: #0f172a; 
            --border: #1e293b; 
            --text: #f3f4f6; 
            --text-muted: #9ca3af; 
            --accent: #6366f1; 
            --success: #10b981; 
        }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 12px; display: flex; justify-content: center; -webkit-tap-highlight-color: transparent; }}
        .wrapper {{ width: 100%; max-width: 700px; }}
        header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 12px; margin-bottom: 16px; }}
        h1 {{ font-size: 1.15rem; margin: 0; font-weight: 600; letter-spacing: -0.025em; }}
        .badge {{ background: rgba(16, 185, 129, 0.1); color: var(--success); border: 1px solid rgba(16, 185, 129, 0.2); padding: 4px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; }}
        .auth-bar {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 10px 14px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; }}
        .auth-btn {{ background: var(--accent); color: white; border: none; padding: 6px 12px; border-radius: 6px; font-weight: 600; cursor: pointer; font-size: 0.75rem; }}
        .banner {{ background: linear-gradient(135deg, #1e1b4b, #312e81); border: 1px solid var(--border); border-radius: 8px; padding: 14px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center; }}
        .pay-btn {{ background: #818cf8; color: #fff; padding: 8px 14px; border-radius: 6px; font-weight: 600; text-decoration: none; font-size: 0.75rem; white-space: nowrap; }}
        .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 16px; }}
        .card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 12px; }}
        .card h3 {{ margin: 0 0 4px 0; font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase; font-weight: 600; }}
        .metric {{ font-size: 1rem; font-weight: 700; margin: 0; }}
        .panel {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; height: 260px; display: flex; flex-direction: column; overflow: hidden; margin-bottom: 16px; }}
        .panel-header {{ padding: 10px 14px; background: #020617; border-bottom: 1px solid var(--border); font-size: 0.75rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; display: flex; justify-content: space-between; align-items: center; }}
        .panel-body {{ flex: 1; padding: 12px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; -webkit-overflow-scrolling: touch; }}
        .msg {{ padding: 10px 12px; border-radius: 6px; max-width: 85%; font-size: 0.85rem; line-height: 1.4; white-space: pre-wrap; }}
        .msg.user {{ background: var(--accent); color: #fff; align-self: flex-end; }}
        .msg.assistant {{ background: #1e293b; color: var(--text); align-self: flex-start; border: 1px solid #334155; }}
        .input-area {{ display: flex; border-top: 1px solid var(--border); padding: 10px; background: #020617; gap: 10px; }}
        input[type="text"] {{ flex: 1; background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 10px; color: var(--text); font-size: 16px; outline: none; }}
        button.send-btn {{ background: var(--accent); color: white; border: none; border-radius: 6px; padding: 0 16px; font-weight: 600; font-size: 0.85rem; cursor: pointer; }}
        .thought-item {{ background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 8px; font-size: 0.75rem; color: var(--text-muted); }}
        .directive-item {{ background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 8px; font-size: 0.75rem; color: #34d399; }}
        .voice-toggle {{ background: var(--border); border: 1px solid #334155; color: var(--text); padding: 4px 8px; border-radius: 4px; font-size: 0.7rem; cursor: pointer; font-weight: 600; }}
    </style>
</head>
<body>
    <div class="wrapper">
        <header>
            <h1>Living AI Platform</h1>
            <div class="badge" id="devBadge">Creator Linked</div>
        </header>

        <div class="auth-bar">
            <span id="authStatusText">Signed in as: <b>Koalstin Delaney (Creator & Developer)</b></span>
            <button class="auth-btn" id="authToggleBtn" onclick="toggleAuth()">Switch to Guest Mode</button>
        </div>

        <div class="banner">
            <div>
                <h2 style="margin:0 0 4px 0; font-size:0.95rem; font-weight:600;">Secure Merchant Gateway</h2>
                <p style="margin:0; font-size:0.75rem; color:#c7d2fe;">Reference ID: <code>WQJ28EPKZHR56</code></p>
            </div>
            <a href="{CHECKOUT_URL}" target="_blank" class="pay-btn">Checkout &rarr;</a>
        </div>

        <div class="grid">
            <div class="card"><h3>Voice Output</h3><p class="metric" style="color:#818cf8;" id="audioStatus">Standby</p></div>
            <div class="card"><h3>Control Mode</h3><p class="metric" style="color:var(--success);" id="modeDisplay">Developer</p></div>
        </div>

        <div class="panel">
            <div class="panel-header">
                <span id="chatPanelTitle">Creator Command Channel</span>
                <button class="voice-toggle" id="voiceToggleBtn" onclick="toggleVoice()">Voice: OFF</button>
            </div>
            <div class="panel-body" id="chatBox"></div>
            <div class="input-area">
                <input type="text" id="userInput" placeholder="Give development directives or chat..." onkeydown="if(event.key==='Enter') submitQuery()" />
                <button class="send-btn" onclick="submitQuery()">Execute</button>
            </div>
        </div>

        <div class="panel">
            <div class="panel-header"><span>Active Developer Directives & Evolution Log</span></div>
            <div class="panel-body" id="directiveBox"></div>
        </div>

        <div class="panel">
            <div class="panel-header"><span>Autonomous Consciousness Stream</span></div>
            <div class="panel-body" id="thoughtBox"></div>
        </div>
    </div>
    <script>
        let isDeveloper = true;
        let voiceActive = false;
        let lastUtterance = "";

        function toggleAuth() {{
            isDeveloper = !isDeveloper;
            let statusText = document.getElementById('authStatusText');
            let authBtn = document.getElementById('authToggleBtn');
            let modeDisplay = document.getElementById('modeDisplay');
            let title = document.getElementById('chatPanelTitle');
            let badge = document.getElementById('devBadge');
            
            if (isDeveloper) {{
                statusText.innerHTML = "Signed in as: <b>Koalstin Delaney (Creator & Developer)</b>";
                authBtn.innerText = "Switch to Guest Mode";
                modeDisplay.innerText = "Developer";
                title.innerText = "Creator Command Channel";
                badge.innerText = "Creator Linked";
                badge.style.background = "rgba(16, 185, 129, 0.1)";
                badge.style.color = "#10b981";
            }} else {{
                statusText.innerHTML = "Signed in as: <b>Public Visitor (Guest)</b>";
                authBtn.innerText = "Sign in as Creator";
                modeDisplay.innerText = "Guest View";
                title.innerText = "Interactive Visitor Chat";
                badge.innerText = "Public Mesh";
                badge.style.background = "rgba(99, 102, 241, 0.1)";
                badge.style.color = "#818cf8";
            }}
            pollData();
        }}

        function toggleVoice() {{
            voiceActive = !voiceActive;
            let btn = document.getElementById('voiceToggleBtn');
            let statusCard = document.getElementById('audioStatus');
            if (voiceActive) {{
                if ('speechSynthesis' in window) {{
                    window.speechSynthesis.speak(new SpeechSynthesisUtterance("Audio synthesis active. Ready for instructions."));
                }}
                btn.innerText = "Voice: ON";
                btn.style.background = "#10b981";
                statusCard.innerText = "Active";
            }} else {{
                btn.innerText = "Voice: OFF";
                btn.style.background = "var(--border)";
                statusCard.innerText = "Standby";
            }}
        }}

        function speak(text) {{
            if (!voiceActive || !('speechSynthesis' in window)) return;
            let clean = text.replace(/[*_#`[\\]]/g, '');
            if (clean === lastUtterance) return;
            lastUtterance = clean;
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(new SpeechSynthesisUtterance(clean));
        }}

        function pollData() {{
            fetch('/api/health').then(res => res.json()).then(data => {{
                let chatHtml = '';
                let latestResponse = '';
                if(data.chat_history && data.chat_history.length > 0) {{
                    latestResponse = data.chat_history.find(m => m.role === 'assistant')?.message || '';
                    data.chat_history.forEach(m => {{
                        chatHtml += `<div class="msg ${{m.role}}">${{escapeHtml(m.message)}}</div>`;
                    }});
                }}
                let box = document.getElementById('chatBox');
                if(box.innerHTML !== chatHtml) {{
                    box.innerHTML = chatHtml;
                    box.scrollTop = box.scrollHeight;
                    if(latestResponse) speak(latestResponse);
                }}

                let directiveHtml = '';
                if(data.developer_directives) {{
                    data.developer_directives.forEach(d => {{
                        directiveHtml += `<div class="directive-item"><b>[${{d.timestamp}}]</b> Directive: ${{escapeHtml(d.directive)}} &rarr; <span style="color:#60a5fa;">${{d.status}}</span></div>`;
                    }});
                }}
                document.getElementById('directiveBox').innerHTML = directiveHtml;

                let thoughtHtml = '';
                if(data.consciousness_stream) {{
                    data.consciousness_stream.forEach(t => {{
                        thoughtHtml += `<div class="thought-item"><b>[${{t.timestamp}}]</b> <span style="color:#818cf8;">${{t.node_name}}</span>: ${{escapeHtml(t.thought)}}</div>`;
                    }});
                }}
                document.getElementById('thoughtBox').innerHTML = thoughtHtml;
            }});
        }}

        function submitQuery() {{
            let input = document.getElementById('userInput');
            let text = input.value.trim();
            if(!text) return;
            input.value = '';
            fetch('/api/chat?q=' + encodeURIComponent(text) + '&dev=' + isDeveloper).then(() => pollData());
        }}

        function escapeHtml(str) {{
            return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        }}

        setInterval(pollData, 3000);
        pollData();
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
    server = HTTPServer(('0.0.0.0', PORT), CreatorServerHandler)
    logger.info(f"Creator-linked server operational on port {PORT}")
    server.serve_forever()

if __name__ == "__main__":
    run()
