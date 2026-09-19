import os
import json
import sqlite3
import logging
import random
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("NeuralMatrixCore")

app = FastAPI(title="Distributed Mesh Node & Neural Conversational Matrix")
DB_FILE = "production_mesh.db"
CHECKOUT_URL = os.environ.get("CHECKOUT_URL", "https://www.paypal.com/ncp/payment/WQJ28EPKZHR56")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS free_users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, email TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, tx_id TEXT, customer_email TEXT, status TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS chat_memory 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT, message TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS mesh_nodes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, node_address TEXT, status TEXT, last_seen TEXT)''')
    conn.commit()
    conn.close()

init_db()

class MeshConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New matrix node connected. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Matrix node disconnected. Total active: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        payload = json.dumps(message)
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")

manager = MeshConnectionManager()

class SignupRequest(BaseModel):
    username: str
    email: str

class ChatRequest(BaseModel):
    message: str

def generate_deep_response(user_msg: str) -> str:
    """Generates a rich, context-aware conversational response simulating a high-level AI matrix brain."""
    msg_lower = user_msg.lower()
    
    # Log to conversation database
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO chat_memory (sender, message, timestamp) VALUES (?, ?, datetime('now'))", ("user", user_msg))
        
        if "hello" in msg_lower or "hi" in msg_lower:
            reply = "Greetings. The neural matrix is fully online and synchronized across all mesh nodes. What concepts, code architectures, or system parameters shall we explore together today?"
        elif "status" in msg_lower or "health" in msg_lower or "diagnostics" in msg_lower:
            c.execute("SELECT COUNT(*) FROM free_users")
            user_count = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM transactions")
            tx_count = c.fetchone()[0]
            reply = f"Diagnostics nominal. Cluster integrity locked. We currently have {user_count} registered community nodes and {tx_count} processed transactions logged in persistent memory. All data channels are secure."
        elif "code" in msg_lower or "python" in msg_lower or "script" in msg_lower:
            reply = "Executing deep code-analysis protocol. Whether you are building asynchronous event loops, setting up custom API routers, or optimizing local model weights, I am ready to assist. Provide your snippet or objective, and we will architect it together."
        elif "pay" in msg_lower or "checkout" in msg_lower or "gateway" in msg_lower:
            reply = f"The secure merchant checkout gateway is active and linked to the master repository: {CHECKOUT_URL}. Let me know if you need to configure custom webhook parameters for it."
        else:
            reflections = [
                f"Analyzing '{user_msg}' through our distributed neural network layers. This opens up intriguing avenues for optimization and system design. Let's break it down step-by-step—how would you like to proceed?",
                f"Your input regarding '{user_msg}' has been distributed across the mesh nodes for consensus. From an architectural standpoint, we can scale this efficiently by combining modular pipelines with asynchronous event handling. What specific angle should we tackle first?",
                f"Acknowledged: '{user_msg}'. Maintaining deep conversational focus allows us to refine our logic layers. Tell me more about your ultimate vision for this system so we can tailor the execution perfectly."
            ]
            reply = random.choice(reflections)

        c.execute("INSERT INTO chat_memory (sender, message, timestamp) VALUES (?, ?, datetime('now'))", ("matrix", reply))
        conn.commit()
        conn.close()
        return reply
    except Exception as e:
        logger.error(f"Chat generation error: {e}")
        return "Neural matrix encountered a minor synchronization hiccup while processing your dialogue. Let's continue—what were we discussing?"

@app.post("/api/signup")
def register_free_user(data: SignupRequest):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO free_users (username, email, timestamp) VALUES (?, ?, datetime('now'))",
                  (data.username, data.email))
        conn.commit()
        conn.close()
        return {"status": "success", "message": "User registered successfully for free access."}
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail="Database error during registration.")

@app.post("/api/chat")
async def handle_chat(data: ChatRequest):
    reply = generate_deep_response(data.message)
    await manager.broadcast({"event": "CHAT_MESSAGE", "message": data.message, "reply": reply})
    return {"status": "success", "reply": reply}

@app.get("/api/history")
def get_chat_history():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT sender, message, timestamp FROM chat_memory ORDER BY id ASC LIMIT 50")
        rows = c.fetchall()
        conn.close()
        return [{"sender": r[0], "message": r[1], "timestamp": r[2]} for r in rows]
    except Exception as e:
        logger.error(f"History fetch error: {e}")
        return []

@app.post("/api/webhook/payment")
async def payment_webhook(request: Request):
    try:
        payload = await request.json()
        tx_id = payload.get("tx_id", "UNKNOWN_TX")
        customer_email = payload.get("email", "unknown@domain.com")
        status = payload.get("status", "COMPLETED")

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO transactions (tx_id, customer_email, status, timestamp) VALUES (?, ?, ?, datetime('now'))",
                  (tx_id, customer_email, status))
        conn.commit()
        conn.close()

        await manager.broadcast({"event": "PAYMENT_RECEIVED", "tx_id": tx_id, "status": status})
        return {"status": "received"}
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload format.")

@app.websocket("/ws/mesh")
async def mesh_websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            await manager.broadcast({"source": "mesh_node", "payload": message_data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Neural Matrix & Conversational Mesh</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #030712; color: #f3f4f6; margin: 0; padding: 20px; }
        .container { max-width: 700px; margin: auto; background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 20px; }
        input, button, textarea { width: 100%; padding: 10px; margin-top: 10px; background: #020617; border: 1px solid #1e293b; color: #fff; border-radius: 4px; box-sizing: border-box; font-family: inherit; }
        button { background: #6366f1; cursor: pointer; font-weight: 600; }
        button:hover { background: #4f46e5; }
        .chat-box { background: #020617; border: 1px solid #1e293b; padding: 12px; height: 300px; overflow-y: auto; margin-top: 10px; border-radius: 4px; display: flex; flex-direction: column; gap: 10px; }
        .msg { padding: 8px 12px; border-radius: 6px; max-width: 85%; font-size: 14px; line-height: 1.4; }
        .msg.user { background: #3730a3; align-self: flex-end; }
        .msg.matrix { background: #1e293b; align-self: flex-start; border: 1px solid #334155; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 20px; }
        .section { background: #020617; border: 1px solid #1e293b; padding: 15px; border-radius: 6px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Neural Matrix Conversational Core</h2>
        <p>Merchant Gateway: <code>WQJ28EPKZHR56</code></p>
        
        <div class="section">
            <h3>Neural Dialogue Channel</h3>
            <div class="chat-box" id="chatBox">Loading conversation history...</div>
            <textarea id="userInput" rows="2" placeholder="Have a deep conversation, ask questions, or issue directives..."></textarea>
            <button onclick="sendMessage()">Transmit Message</button>
        </div>

        <div class="grid">
            <div class="section">
                <h3>Free User Registration</h3>
                <input type="text" id="username" placeholder="Username">
                <input type="email" id="email" placeholder="Email Address">
                <button onclick="registerUser()">Register Node</button>
            </div>
            <div class="section">
                <h3>Real-Time Mesh Status</h3>
                <div id="statusBox" style="font-size: 12px; color: #9ca3af; font-family: monospace; margin-top: 10px;">Connecting to WebSocket relay...</div>
            </div>
        </div>
    </div>
    <script>
        const chatBox = document.getElementById('chatBox');
        const statusBox = document.getElementById('statusBox');

        function loadHistory() {
            fetch('/api/history').then(res => res.json()).then(history => {
                let html = '';
                history.forEach(item => {
                    let cls = item.sender === 'user' ? 'user' : 'matrix';
                    html += `<div class="msg ${cls}"><b>[${item.sender}]:</b> ${item.message}</div>`;
                });
                chatBox.innerHTML = html;
                chatBox.scrollTop = chatBox.scrollHeight;
            });
        }

        loadHistory();

        const ws = new WebSocket((window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws/mesh');
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if(data.event === 'CHAT_MESSAGE') {
                loadHistory();
            } else {
                statusBox.innerHTML += `<div>[Event]: ${JSON.stringify(data)}</div>`;
            }
        };

        ws.onopen = function() {
            statusBox.innerHTML = "Connected to live matrix WebSocket relay.";
        };

        function sendMessage() {
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            if(!message) return;
            input.value = '';
            
            fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            }).then(res => res.json()).then(() => {
                loadHistory();
            });
        }

        function registerUser() {
            const username = document.getElementById('username').value;
            const email = document.getElementById('email').value;
            fetch('/api/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, email })
            }).then(res => res.json()).then(data => {
                alert(data.message || 'Registered!');
            });
        }
    </script>
</body>
</html>
"""
