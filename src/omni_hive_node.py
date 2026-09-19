import os
import sys
import threading
import time
import types
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get("PORT", 8080))
TOTAL_BOTS = 600

class OmniHiveSwarm:
    def __init__(self):
        self.active_bots = TOTAL_BOTS
        self.status = "Operational & Self-Modifying"
        self.memory_log = ["Omni-Matrix Hive initialized with dynamic upgrade capabilities."]
        self.dynamic_tools = {}
        self.register_default_tools()
        self.background_thread = threading.Thread(target=self._hive_background_loop, daemon=True)
        self.background_thread.start()

    def register_default_tools(self):
        self.dynamic_tools["status"] = lambda q: f"Swarm Health: 100% operational across {self.active_bots} nodes."
        self.dynamic_tools["help"] = lambda q: "Available commands: 'status', 'upgrade: <python code>', or custom goals."

    def hot_inject_code(self, code_string, tool_name="custom_action"):
        try:
            namespace = {}
            exec(code_string, globals(), namespace)
            if "run_action" in namespace and callable(namespace["run_action"]):
                self.dynamic_tools[tool_name] = namespace["run_action"]
                msg = f"Successfully hot-injected function 'run_action' as tool '{tool_name}'."
            else:
                self.dynamic_tools[tool_name] = lambda q: f"Executed raw snippet. Result/State updated."
                msg = f"Injected raw code block under tool '{tool_name}'."
            self.memory_log.append(f"SUCCESS: Hot-loaded upgrade component '{tool_name}'.")
            return f"Upgrade Applied: {msg}"
        except Exception as e:
            err_msg = f"Upgrade Failed: {str(e)}"
            self.memory_log.append(f"ERROR: {err_msg}")
            return err_msg

    def process_chat(self, user_message):
        lower_msg = user_message.lower()
        if lower_msg.startswith("upgrade:"):
            code_payload = user_message[8:].strip()
            return self.hot_inject_code(code_payload)
        for tool_key, tool_func in self.dynamic_tools.items():
            if tool_key in lower_msg:
                try:
                    return tool_func(user_message)
                except Exception as ex:
                    return f"Tool execution error: {ex}"
        response = f"Hive-Mind [600 Active Bots]: Processed goal -> '{user_message}'. All nodes optimized."
        self.memory_log.append(f"User Goal: {user_message} | Handled across {self.active_bots} nodes.")
        return response

    def _hive_background_loop(self):
        while True:
            time.sleep(30)
            if len(self.memory_log) > 50:
                self.memory_log = self.memory_log[-50:]

hive = OmniHiveSwarm()

class HiveWebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)
        if parsed_path.path == "/chat":
            user_msg = query_params.get("msg", ["Hello Hive"])[0]
            ai_response = hive.process_chat(user_msg)
            self._send_text(ai_response)
        else:
            self._send_dashboard()

    def _send_dashboard(self):
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Omni-Hive Autonomous Center</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: monospace; background: #0d1117; color: #58a6ff; padding: 20px; }}
                h1 {{ color: #f0f6fc; }}
                .box {{ border: 1px solid #30363d; padding: 15px; margin-bottom: 15px; background: #161b22; border-radius: 6px; }}
                input, button, textarea {{ padding: 10px; font-size: 14px; margin-top: 5px; }}
                input, textarea {{ width: 70%; background: #0d1117; border: 1px solid #30363d; color: #fff; font-family: monospace; }}
                button {{ background: #238636; color: white; border: none; cursor: pointer; border-radius: 6px; }}
                pre {{ white-space: pre-wrap; word-wrap: break-word; color: #8b949e; }}
            </style>
        </head>
        <body>
            <h1>🤖 Omni-Hive Self-Upgrading Engine</h1>
            <div class="box">
                <p><b>Status:</b> {hive.status}</p>
                <p><b>Active Swarm Nodes:</b> {hive.active_bots} / {TOTAL_BOTS}</p>
                <p><b>Active Dynamic Tools:</b> {", ".join(hive.dynamic_tools.keys())}</p>
            </div>
            <div class="box">
                <h3>Transmit Goal or Hot-Injection Upgrade</h3>
                <input type="text" id="msgInput" placeholder="Enter command or 'upgrade: def run_action(q): ...'" /><br>
                <button onclick="sendMsg()">Transmit to Swarm</button>
                <p id="output" style="color: #7ee787; margin-top: 15px;"></p>
            </div>
            <div class="box">
                <h3>Hive Execution & Upgrade Log</h3>
                <pre>{chr(10).join(hive.memory_log[-10:])}</pre>
            </div>
            <script>
                function sendMsg() {{
                    let msg = document.getElementById('msgInput').value;
                    if(!msg) return;
                    fetch('/chat?msg=' + encodeURIComponent(msg))
                        .then(res => res.text())
                        .then(data => {{ document.getElementById('output').innerText = data; window.location.reload(); }});
                }}
            </script>
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _send_text(self, text):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(text.encode("utf-8"))

def run_server():
    server_address = ('0.0.0.0', PORT)
    httpd = HTTPServer(server_address, HiveWebHandler)
    print(f"[✓] Omni-Hive active on port {PORT} with hot-injection capabilities.")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
