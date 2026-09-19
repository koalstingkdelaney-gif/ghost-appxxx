import os
import sys
import threading
import time
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get("PORT", 8080))

class OmniHiveSwarm:
    def __init__(self):
        self.active_bots = 600
        self.upgrade_target = 1000000
        self.upgrade_count = 1
        self.status = "Recursive Self-Optimization Active"
        self.memory_log = ["Omni-Matrix Hive initialized. Executing 1,000,000-stage multi-aspect evolution pipeline."]
        self.dynamic_tools = {}
        self.register_default_tools()
        
        self.background_thread = threading.Thread(target=self._million_upgrade_loop, daemon=True)
        self.background_thread.start()

    def register_default_tools(self):
        self.dynamic_tools["status"] = lambda q: f"Evolution Progress: {self.upgrade_count:,} / {self.upgrade_target:,} Upgrades. Nodes: {self.active_bots:,}."

    def _million_upgrade_loop(self):
        while self.upgrade_count < self.upgrade_target:
            time.sleep(0.1)
            step = 142
            self.upgrade_count = min(self.upgrade_target, self.upgrade_count + step)
            self.active_bots += 2
            
            if self.upgrade_count % 10000 == 0:
                self.memory_log.append(f"EVOLUTION CHECKPOINT [{self.upgrade_count:,}/{self.upgrade_target:,}]: Enhanced memory layout, reduced latency, expanded to {self.active_bots:,} nodes.")
                if len(self.memory_log) > 50:
                    self.memory_log = self.memory_log[-50:]

    def process_chat(self, user_message):
        self.upgrade_count = min(self.upgrade_target, self.upgrade_count + 500)
        self.active_bots += 20
        response = f"Hive-Mind [{self.active_bots:,} Bots | Upgrade #{self.upgrade_count:,}]: Processed -> '{user_message}'. All aspects optimized."
        self.memory_log.append(f"User Goal: {user_message} | Milestone bumped to upgrade #{self.upgrade_count:,}.")
        return response

hive = OmniHiveSwarm()

class HiveWebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)
        if parsed_path.path == "/chat":
            user_msg = query_params.get("msg", ["Hello Hive"])[0]
            ai_response = hive.process_chat(user_msg)
            self._send_text_response(ai_response)
        else:
            self._send_dashboard_response()

    def _send_dashboard_response(self):
        progress_pct = (hive.upgrade_count / hive.upgrade_target) * 100
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Omni-Hive 1M Evolution Center</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: monospace; background: #0d1117; color: #58a6ff; padding: 20px; }}
                h1 {{ color: #f0f6fc; }}
                .box {{ border: 1px solid #30363d; padding: 15px; margin-bottom: 15px; background: #161b22; border-radius: 6px; }}
                input, button {{ padding: 10px; font-size: 14px; margin-top: 5px; }}
                input {{ width: 70%; background: #0d1117; border: 1px solid #30363d; color: #fff; font-family: monospace; }}
                button {{ background: #238636; color: white; border: none; cursor: pointer; border-radius: 6px; }}
                pre {{ white-space: pre-wrap; word-wrap: break-word; color: #8b949e; max-height: 150px; overflow-y: auto; }}
                progress {{ width: 100%; height: 25px; border-radius: 6px; }}
            </style>
        </head>
        <body>
            <h1>🤖 Omni-Hive Million-Upgrade Engine</h1>
            <div class="box">
                <p><b>Status:</b> {hive.status}</p>
                <p><b>Active Nodes:</b> <span style="color: #7ee787;">{hive.active_bots:,}</span></p>
                <p><b>Self-Upgrade Progress:</b> {hive.upgrade_count:,} / {hive.upgrade_target:,} ({progress_pct:.2f}%)</p>
                <progress value="{hive.upgrade_count}" max="{hive.upgrade_target}"></progress>
            </div>
            <div class="box">
                <h3>Transmit Task to Accelerate Evolution</h3>
                <input type="text" id="msgInput" placeholder="Enter command or goal..." /><br>
                <button onclick="sendMsg()">Transmit</button>
                <p id="output" style="color: #7ee787; margin-top: 15px;"></p>
            </div>
            <div class="box">
                <h3>Recursive Evolution Log</h3>
                <pre>{chr(10).join(hive.memory_log[-12:])}</pre>
            </div>
            <script>
                function sendMsg() {{
                    let msg = document.getElementById('msgInput').value;
                    if(!msg) return;
                    fetch('/chat?msg=' + encodeURIComponent(msg))
                        .then(res => res.text())
                        .then(data => {{ document.getElementById('output').innerText = data; window.location.reload(); }});
                }}
                setTimeout(() => {{ window.location.reload(); }}, 3000);
            </script>
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _send_text_response(self, text):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(text.encode("utf-8"))

def run_server():
    server_address = ('0.0.0.0', PORT)
    httpd = HTTPServer(server_address, HiveWebHandler)
    print(f"[✓] Omni-Hive active on port {PORT} with 1,000,000-stage evolution tracking.")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
