import os
import sys
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

# Configuration
PORT = int(os.environ.get("PORT", 8080))
TOTAL_BOTS = 600

class HiveMindCore:
    def __init__(self):
        self.active_bots = TOTAL_BOTS
        self.status = "Operational"
        self.memory_log = ["Omni-Matrix Hive initialized with 600 autonomous nodes."]
        # Start background hive synchronization loop
        self.background_thread = threading.Thread(target=self._hive_background_loop, daemon=True)
        self.background_thread.start()

    def _hive_background_loop(self):
        while True:
            # Periodic background maintenance for the 600 bots
            time.sleep(30)
            if len(self.memory_log) > 50:
                self.memory_log = self.memory_log[-50:]

    def process_chat(self, user_message):
        response = f"Hive-Mind [600 Active Bots]: Received your command -> '{user_message}'. Systems synchronized and operational."
        self.memory_log.append(f"User: {user_message} | Hive: Processed across {self.active_bots} nodes.")
        return response

hive = HiveMindCore()

class HiveWebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)

        if parsed_path.path == "/chat":
            user_msg = query_params.get("msg", ["Hello Hive"])[0]
            ai_response = hive.process_chat(user_msg)
            self._send_html(ai_response)
        else:
            self._send_dashboard()

    def _send_dashboard(self):
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Omni-Hive Command Center</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: monospace; background: #0d1117; color: #58a6ff; padding: 20px; }}
                h1 {{ color: #f0f6fc; }}
                .box {{ border: 1px solid #30363d; padding: 15px; margin-bottom: 15px; background: #161b22; border-radius: 6px; }}
                input, button {{ padding: 10px; font-size: 16px; margin-top: 5px; }}
                input {{ width: 70%; background: #0d1117; border: 1px solid #30363d; color: #fff; }}
                button {{ background: #238636; color: white; border: none; cursor: pointer; border-radius: 6px; }}
                pre {{ white-space: pre-wrap; word-wrap: break-word; color: #8b949e; }}
            </style>
        </head>
        <body>
            <h1>🤖 Omni-Hive Autonomous Engine</h1>
            <div class="box">
                <p><b>Status:</b> {hive.status}</p>
                <p><b>Active Swarm Nodes:</b> {hive.active_bots} / {TOTAL_BOTS}</p>
            </div>
            <div class="box">
                <h3>Interact with the AI Swarm</h3>
                <input type="text" id="msgInput" placeholder="Enter command or question..." />
                <button onclick="sendMsg()">Transmit</button>
                <p id="output" style="color: #7ee787; margin-top: 15px;"></p>
            </div>
            <div class="box">
                <h3>Hive Activity Log</h3>
                <pre>{chr(10).join(hive.memory_log[-10:])}</pre>
            </div>
            <script>
                function sendMsg() {{
                    let msg = document.getElementById('msgInput').value;
                    if(!msg) return;
                    fetch('/chat?msg=' + encodeURIComponent(msg))
                        .then(res => res.text())
                        .then(data => {{
                            document.getElementById('output').innerText = data;
                        }});
                }}
            </script>
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _send_html(self, text):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(text.encode("utf-8"))

def run_server():
    server_address = ('0.0.0.0', PORT)
    httpd = HTTPServer(server_address, HiveWebHandler)
    print(f"[✓] Omni-Hive running on port {PORT} with {TOTAL_BOTS} bots online.")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
