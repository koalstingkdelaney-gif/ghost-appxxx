import os
import json
import sqlite3
import logging
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("MeshNetworkCore")

app = FastAPI(title="Distributed Mesh Node & Payment Gateway")
DB_FILE = "production_mesh.db"
CHECKOUT_URL = os.environ.get("CHECKOUT_URL", "https://www.paypal.com/ncp/payment/WQJ28EPKZHR56")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS free_users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, email TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, tx_id TEXT, customer_email TEXT, status TEXT, timestamp TEXT)''')
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
        logger.info(f"New mesh node connected. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Mesh node disconnected. Total active: {len(self.active_connections)}")

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

        await manager.broadcast({
            "event": "PAYMENT_RECEIVED",
            "tx_id": tx_id,
            "status": status
        })

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
            await manager.broadcast({
                "source": "mesh_node",
                "payload": message_data
            })
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
    <title>Distributed Mesh Node & Gateway</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #030712; color: #f3f4f6; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: auto; background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 20px; }
        input, button { width: 100%; padding: 10px; margin-top: 10px; background: #020617; border: 1px solid #1e293b; color: #fff; border-radius: 4px; box-sizing: border-box; }
        button { background: #6366f1; cursor: pointer; font-weight: 600; }
        .log-box { background: #020617; border: 1px solid #1e293b; padding: 10px; height: 150px; overflow-y: auto; font-family: monospace; font-size: 12px; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Mesh Node & Community Portal</h2>
        <p>Checkout Gateway: <code>WQJ28EPKZHR56</code></p>
        
        <h3>Free User Registration</h3>
        <input type="text" id="username" placeholder="Username">
        <input type="email" id="email" placeholder="Email Address">
        <button onclick="registerUser()">Sign Up Free</button>

        <h3>Live Mesh Node Telemetry</h3>
        <div class="log-box" id="logBox">Connecting to WebSocket...</div>
    </div>
    <script>
        const logBox = document.getElementById('logBox');
        const ws = new WebSocket((window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws/mesh');

        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            logBox.innerHTML += `<div>[Mesh Event] ${JSON.stringify(data)}</div>`;
            logBox.scrollTop = logBox.scrollHeight;
        };

        ws.onopen = function() {
            logBox.innerHTML += `<div>Connected to mesh network.</div>`;
        };

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
