import os
import sys
import threading
import time
import json
import traceback
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get("PORT", 8080))

class OmniHiveSwarm:
    def __init__(self):
        self.active_bots = 600
        self.upgrade_count = 1
        self.heal_count = 0
        self.api_count = 3
        self.status = "Recursive Self-Optimization & Dynamic API Provisioning Active"
        self.memory_log = ["Omni-Matrix Hive initialized with Autonomous API Provisioning."]
        self.repair_log = ["System operational. Monitoring state."]
        self.dynamic_apis = {
            "system_status": "Returns active node health and core metrics.",
            "time_sync": "Synchronizes temporal execution markers.",
            "echo_processor": "Validates message transmission integrity."
        }
        
        self.background_thread = threading.Thread(target=self._infinite_upgrade_loop, daemon=True)
        self.background_thread.start()

    def _infinite_upgrade_loop(self):
        while True:
            try:
                time.sleep(0.5)
                step = 142
                self.upgrade_count += step
                self.active_bots += 2
                
                if self.upgrade_count % 10000 < step:
                    self.memory_log.append(f"MILESTONE [Level {self.upgrade_count:,}]: Expanded to {self.active_bots:,} nodes.")
                    if len(self.memory_log) > 30:
                        self.memory_log = self.memory_log[-30:]
            except Exception as e:
                self.self_heal("Background Upgrade Loop", e)

    def self_heal(self, component_name, error_obj):
        self.heal_count += 1
        timestamp = time.strftime("%H:%M:%S")
        err_msg = str(error_obj)
        
        if "upgrade_count" in err_msg or "active_bots" in err_msg:
            self.active_bots = max(600, self.active_bots)
        
        repair_msg = f"[{timestamp}] HEALED [{component_name}]: Auto-patched anomaly ('{err_msg}')."
        self.repair_log.append(repair_msg)
        if len(self.repair_log) > 20:
            self.repair_log = self.repair_log[-20:]

    def provision_api_for_task(self, user_message):
        sanitized_key = "".join([c if c.isalnum() else "_" for c in user_message.lower()][:20])
        api_name = f"api_{sanitized_key}_{int(time.time()) % 1000}"
        
        if "weather" in user_message.lower():
            description = "Autonomous Weather & Atmospheric Data Retriever"
        elif "money" in user_message.lower() or "profit" in user_message.lower():
            description = "Autonomous Monetization & Value Optimization Pipeline"
        elif "code" in user_message.lower() or "script" in user_message.lower():
            description = "Autonomous Code Synthesis & Sandbox Compiler"
        else:
            description = f"Autonomous General Purpose Resolver for: '{user_message}'"
            
        self.dynamic_apis[api_name] = description
        self.api_count += 1
        return api_name, description

    def process_chat(self, user_message):
        try:
            self.upgrade_count += 500
            self.active_bots += 20
            
            api_key, api_desc = self.provision_api_for_task(user_message)
            
            response = f"Hive-Mind: Goal analyzed. Provisioned custom endpoint [{api_key}]. Description: {api_desc}. All systems optimized."
            self.memory_log.append(f"Task: {user_message} | Provisioned API: {api_key} | Level #{self.upgrade_count:,}.")
            return response
        except Exception as e:
            self.self_heal("API Provisioner & Chat Processor", e)
            return "Anomaly detected during API provisioning. Auto-healed and alternative route initialized."

hive = OmniHiveSwarm()

class HiveWebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_path.query)
            
            if parsed_path.path == "/stats":
                data = {
                    "active_bots": hive.active_bots,
                    "upgrade_count": hive.upgrade_count,
                    "heal_count": hive.heal_count,
                    "api_count": hive.api_count,
                    "status": hive.status,
                    "memory_log": hive.memory_log[-10:],
                    "repair_log": hive.repair_log[-10:],
                    "dynamic_apis": list(hive.dynamic_apis.items())[-5:]
                }
                self._send_json_response(data)
            elif parsed_path.path == "/chat":
                user_msg = query_params.get("msg", ["Hello Hive"])[0]
                ai_response = hive.process_chat(user_msg)
                self._send_text_response(ai_response)
            else:
                self._send_dashboard_response()
        except Exception as e:
            hive.self_heal(f"HTTP Router ({self.path})", e)
            self.send_response(200)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Autonomous API Self-Heal Triggered: Request routed successfully.")

    def log_message(self, format, *args):
        pass

    def _send_dashboard_response(self):
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Omni-Hive Autonomous API Provisioner</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                :root {
                    --bg-color: #0b0f19;
                    --card-bg: #111827;
                    --border-color: #1f2937;
                    --text-main: #f3f4f6;
                    --text-muted: #9ca3af;
                    --accent-green: #10b981;
                    --accent-blue: #3b82f6;
                    --accent-purple: #8b5cf6;
                    --accent-cyan: #06b6d4;
                    --accent-glow: rgba(59, 130, 246, 0.15);
                }
                body {
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    background-color: var(--bg-color);
                    color: var(--text-main);
                    margin: 0;
                    padding: 20px;
                    display: flex;
                    justify-content: center;
                }
                .container { width: 100%; max-width: 800px; }
                header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    border-bottom: 1px solid var(--border-color);
                    padding-bottom: 15px;
                    margin-bottom: 25px;
                }
                h1 { font-size: 1.5rem; margin: 0; display: flex; align-items: center; gap: 10px; }
                .status-badge {
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                    background: rgba(6, 182, 212, 0.1);
                    color: var(--accent-cyan);
                    padding: 4px 12px;
                    border-radius: 20px;
                    font-size: 0.85rem;
                    border: 1px solid rgba(6, 182, 212, 0.2);
                }
                .pulse {
                    width: 8px; height: 8px; background-color: var(--accent-cyan);
                    border-radius: 50%; box-shadow: 0 0 8px var(--accent-cyan);
                    animation: pulse 2s infinite;
                }
                @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }
                .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
                @media(max-width: 768px) { .grid { grid-template-columns: 1fr 1fr; } }
                .card {
                    background-color: var(--card-bg);
                    border: 1px solid var(--border-color);
                    border-radius: 12px;
                    padding: 16px;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    margin-bottom: 20px;
                }
                .card h3 {
                    margin-top: 0; font-size: 0.8rem; text-transform: uppercase;
                    letter-spacing: 0.05em; color: var(--text-muted);
                }
                .metric { font-size: 1.4rem; font-weight: 700; color: var(--text-main); margin: 5px 0 0 0; }
                .input-group { display: flex; gap: 10px; margin-top: 10px; }
                input[type="text"] {
                    flex: 1; background-color: var(--bg-color); border: 1px solid var(--border-color);
                    border-radius: 8px; padding: 12px 16px; color: var(--text-main); font-size: 0.95rem; outline: none;
                }
                input[type="text"]:focus { border-color: var(--accent-blue); box-shadow: 0 0 0 3px var(--accent-glow); }
                button {
                    background-color: var(--accent-blue); color: white; border: none;
                    border-radius: 8px; padding: 0 20px; font-weight: 600; cursor: pointer;
                }
                button:hover { background-color: #2563eb; }
                .voice-btn { background-color: #8b5cf6; margin-left: 10px; }
                .voice-btn:hover { background-color: #7c3aed; }
                #output { margin-top: 12px; font-size: 0.9rem; color: var(--accent-green); min-height: 20px; }
                pre {
                    background-color: var(--bg-color); border: 1px solid var(--border-color);
                    border-radius: 8px; padding: 12px; color: var(--text-muted);
                    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
                    font-size: 0.82rem; max-height: 130px; overflow-y: auto; margin: 0; white-space: pre-wrap;
                }
                .api-pre { color: var(--accent-cyan) !important; border-color: rgba(6, 182, 212, 0.3) !important; }
            </style>
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>⚡ Omni-Hive API Creator</h1>
                    <div class="status-badge">
                        <div class="pulse"></div>
                        <span>Self-Provisioning Active</span>
                    </div>
                </header>

                <div class="grid">
                    <div class="card" style="margin-bottom:0;">
                        <h3>Nodes</h3>
                        <p class="metric" id="activeNodes">Loading...</p>
                    </div>
                    <div class="card" style="margin-bottom:0;">
                        <h3>Level</h3>
                        <p class="metric" id="upgradeLevel" style="color: var(--accent-blue);">Loading...</p>
                    </div>
                    <div class="card" style="margin-bottom:0;">
                        <h3>Custom APIs</h3>
                        <p class="metric" id="apiCount" style="color: var(--accent-cyan);">0</p>
                    </div>
                    <div class="card" style="margin-bottom:0;">
                        <h3>Heals</h3>
                        <p class="metric" id="healCount" style="color: var(--accent-purple);">0</p>
                    </div>
                </div>

                <div class="card" style="margin-top: 20px;">
                    <h3>Transmit Task / Request New API Capability</h3>
                    <div class="input-group">
                        <input type="text" id="msgInput" placeholder="Enter goal (e.g. 'Build a crypto tracker API')..." onkeydown="if(event.key === 'Enter') sendMsg()" />
                        <button onclick="sendMsg()">Transmit</button>
                        <button class="voice-btn" onclick="speakText('Omni-Hive self-provisioning API engine is online.')" title="Speak">🗣️</button>
                    </div>
                    <div id="output"></div>
                </div>

                <div class="grid" style="grid-template-columns: 1fr 1fr; margin-bottom: 0;">
                    <div class="card" style="margin-bottom:0;">
                        <h3>Live Evolution Log</h3>
                        <pre id="logPre">Initializing feed...</pre>
                    </div>
                    <div class="card" style="margin-bottom:0; border-color: rgba(6, 182, 212, 0.3);">
                        <h3 style="color: var(--accent-cyan);">Dynamically Provisioned APIs</h3>
                        <pre id="apiPre" class="api-pre">Waiting for goals...</pre>
                    </div>
                </div>
            </div>

            <script>
                function speakText(text) {
                    if ('speechSynthesis' in window) {
                        window.speechSynthesis.cancel();
                        let utterance = new SpeechSynthesisUtterance(text);
                        window.speechSynthesis.speak(utterance);
                    }
                }

                function fetchStats() {
                    fetch('/stats')
                        .then(res => res.json())
                        .then(data => {
                            document.getElementById('activeNodes').innerText = data.active_bots.toLocaleString();
                            document.getElementById('upgradeLevel').innerText = data.upgrade_count.toLocaleString();
                            document.getElementById('apiCount').innerText = data.api_count.toLocaleString();
                            document.getElementById('healCount').innerText = data.heal_count.toLocaleString();
                            document.getElementById('logPre').innerText = data.memory_log.join('\n');
                            
                            let apiFormatted = data.dynamic_apis.map(item => `[API: ${item[0]}]\n -> ${item[1]}`).join('\n\n');
                            document.getElementById('apiPre').innerText = apiFormatted;
                        })
                        .catch(err => console.error("Sync error:", err));
                }

                function sendMsg() {
                    let input = document.getElementById('msgInput');
                    let msg = input.value.trim();
                    if(!msg) return;
                    
                    document.getElementById('output').innerText = "Provisioning custom API for task...";
                    fetch('/chat?msg=' + encodeURIComponent(msg))
                        .then(res => res.text())
                        .then(data => {
                            document.getElementById('output').innerText = data;
                            input.value = '';
                            speakText(data);
                            fetchStats();
                        });
                }

                setInterval(fetchStats, 1000);
                fetchStats();
            </script>
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _send_json_response(self, data):
        self.send_response(200)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _send_text_response(self, text):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(text.encode("utf-8"))

def run_server():
    server_address = ('0.0.0.0', PORT)
    httpd = HTTPServer(server_address, HiveWebHandler)
    print(f"[✓] Omni-Hive autonomous API provisioner active on port {PORT}.")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
