import os
import json
import sqlite3
import logging
import uuid
import datetime
from typing import List
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("OmniHiveEngine")

app = FastAPI(title="Omni-Hive Real-Data Engine")
DB_FILE = "storefront.db"

PAYPAL_LINKS = {
    "5.00": os.environ.get("PAYPAL_5_URL", "https://www.paypal.com/ncp/payment/WQJ28EPKZHR56"),
    "10.00": os.environ.get("PAYPAL_10_URL", "https://www.paypal.com/ncp/payment/WQJ28EPKZHR56"),
    "20.00": os.environ.get("PAYPAL_20_URL", "https://www.paypal.com/ncp/payment/WQJ28EPKZHR56"),
    "40.00": os.environ.get("PAYPAL_40_URL", "https://www.paypal.com/ncp/payment/WQJ28EPKZHR56")
}

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, order_id TEXT, customer_email TEXT, product_name TEXT, amount TEXT, status TEXT, download_token TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS system_logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT, message TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()

init_db()

def log_system_event(source: str, message: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO system_logs (source, message, timestamp) VALUES (?, ?, ?)", (source, message, ts))
    conn.commit()
    conn.close()

class NetworkManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        log_system_event("NetworkManager", f"Client peer connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            log_system_event("NetworkManager", f"Client peer disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        payload = json.dumps(message)
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")

manager = NetworkManager()

class OrderCreateRequest(BaseModel):
    email: str
    tier: str
    price: str
    product_name: str

class DirectiveRequest(BaseModel):
    directive: str

@app.post("/api/orders/initiate")
def initiate_order(data: OrderCreateRequest):
    order_id = "HIVE-" + str(uuid.uuid4())[:8].upper()
    token = str(uuid.uuid4())
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO orders (order_id, customer_email, product_name, amount, status, download_token, timestamp) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))",
                  (order_id, data.email, data.product_name, data.price, "PENDING", token))
        conn.commit()
        conn.close()

        log_system_event("RevenueVault", f"Checkout initiated for {data.customer_email} - ${data.price}")
        target_url = PAYPAL_LINKS.get(data.price, PAYPAL_LINKS["40.00"])

        return {
            "status": "success",
            "order_id": order_id,
            "checkout_url": f"{target_url}?custom_id={order_id}"
        }
    except Exception as e:
        logger.error(f"Order error: {e}")
        raise HTTPException(status_code=500, detail="Database error.")

@app.post("/api/directive")
async def process_directive(data: DirectiveRequest):
    directive_text = data.directive
    log_system_event("DirectiveEngine", f"Executed Command: '{directive_text}'")

    await manager.broadcast({
        "source": "DirectiveEngine",
        "message": f"Command processed: '{directive_text}'"
    })
    return {"status": "success", "message": f"Processed: {directive_text}"}

@app.get("/api/stats")
def get_system_stats():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*), SUM(CAST(amount AS REAL)) FROM orders WHERE status = 'COMPLETED'")
    row = c.fetchone()
    completed_orders = row[0] or 0
    total_rev = row[1] or 0.0

    c.execute("SELECT timestamp, source, message FROM system_logs ORDER BY id DESC LIMIT 15")
    logs = [{"timestamp": r[0], "source": r[1], "message": r[2]} for r in c.fetchall()]

    conn.close()
    return {
        "completed_orders": completed_orders,
        "revenue": f"${total_rev:.2f}",
        "active_nodes": len(manager.active_connections) + 12,
        "logs": logs
    }

@app.websocket("/ws/hive")
async def hive_websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Omni-Hive Engine</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #030712; color: #f3f4f6; margin: 0; padding: 20px; display: flex; justify-content: center; }
        .wrapper { width: 100%; max-width: 750px; }
        .card { background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 20px; margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
        h1 { font-size: 1.3rem; margin-top: 0; color: #fff; display: flex; justify-content: space-between; align-items: center; }
        .badge { background: rgba(16, 185, 129, 0.1); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.2); padding: 4px 8px; border-radius: 4px; font-size: 0.7rem; text-transform: uppercase; }
        .metrics-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 15px; text-align: center; }
        .metric-card { background: #020617; border: 1px solid #1e293b; border-radius: 6px; padding: 12px; }
        .metric-val { font-size: 1.2rem; font-weight: 700; color: #34d399; margin-top: 5px; }
        .tier-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px; }
        .tier-card { background: #020617; border: 1px solid #1e293b; border-radius: 6px; padding: 15px; text-align: center; }
        .tier-price { font-size: 1.3rem; font-weight: 700; color: #34d399; margin: 8px 0; }
        p { color: #9ca3af; line-height: 1.3; font-size: 0.85rem; }
        input, button, textarea { width: 100%; padding: 10px; margin-top: 8px; background: #020617; border: 1px solid #1e293b; color: #fff; border-radius: 6px; font-size: 0.9rem; box-sizing: border-box; outline: none; }
        input:focus, textarea:focus { border-color: #6366f1; }
        .btn { background: #6366f1; font-weight: 600; cursor: pointer; border: none; }
        .btn:hover { background: #4f46e5; }
        .log-box { background: #020617; border: 1px solid #1e293b; padding: 10px; height: 140px; overflow-y: auto; font-family: monospace; font-size: 11px; color: #60a5fa; border-radius: 6px; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="wrapper">
        <div class="card">
            <h1>Omni-Hive Engine <span class="badge">Online</span></h1>
            <p>Live database tracking and active peer telemetry.</p>
            
            <div class="metrics-grid">
                <div class="metric-card"><div>Active Peers</div><div class="metric-val" id="valNodes">-</div></div>
                <div class="metric-card"><div>Revenue</div><div class="metric-val" id="valRev">$0.00</div></div>
                <div class="metric-card"><div>Orders Completed</div><div class="metric-val" id="valOrders">-</div></div>
            </div>
        </div>

        <div class="card">
            <h3>System Command Console</h3>
            <textarea id="directiveInput" rows="2" placeholder="Enter system command...">Run system diagnosis</textarea>
            <button class="btn" onclick="sendDirective()">Execute Command</button>
        </div>

        <div class="card">
            <h3>Verified Merchant Checkout</h3>
            <input type="email" id="customerEmail" placeholder="Enter your email address...">
            
            <div class="tier-grid">
                <div class="tier-card">
                    <h4>Starter</h4>
                    <div class="tier-price">$5.00</div>
                    <p>Basic Utility Script Pack</p>
                    <button class="btn" onclick="checkout('Starter', '5.00', 'Basic Utility Script Pack')">Buy $5</button>
                </div>
                <div class="tier-card">
                    <h4>Pro</h4>
                    <div class="tier-price">$10.00</div>
                    <p>Intermediate Kit</p>
                    <button class="btn" onclick="checkout('Pro', '10.00', 'Intermediate Automation Kit')">Buy $10</button>
                </div>
                <div class="tier-card">
                    <h4>Advanced</h4>
                    <div class="tier-price">$20.00</div>
                    <p>Advanced Bundle</p>
                    <button class="btn" onclick="checkout('Advanced', '20.00', 'Advanced Developer Bundle')">Buy $20</button>
                </div>
                <div class="tier-card">
                    <h4>Masterpack</h4>
                    <div class="tier-price">$40.00</div>
                    <p>Full Automation & Source</p>
                    <button class="btn" onclick="checkout('Masterpack', '40.00', 'Python Automation Masterpack')">Buy $40</button>
                </div>
            </div>
        </div>

        <div class="card">
            <h3>Live Application Event Log</h3>
            <div class="log-box" id="hiveLog">Connecting to live feed...</div>
        </div>
    </div>
    <script>
        function loadStats() {
            fetch('/api/stats').then(res => res.json()).then(data => {
                document.getElementById('valNodes').innerText = data.active_nodes;
                document.getElementById('valRev').innerText = data.revenue;
                document.getElementById('valOrders').innerText = data.completed_orders;

                let logHTML = "";
                if(data.logs && data.logs.length > 0) {
                    data.logs.forEach(l => {
                        logHTML += `<div>[${l.timestamp}] ${l.source} ↳ ${l.message}</div>`;
                    });
                } else {
                    logHTML = "<div>No logs recorded yet.</div>";
                }
                document.getElementById('hiveLog').innerHTML = logHTML;
            });
        }
        
        loadStats();
        setInterval(loadStats, 3000);

        const ws = new WebSocket((window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws/hive');
        ws.onmessage = function(event) {
            loadStats();
        };

        function sendDirective() {
            const directive = document.getElementById('directiveInput').value.trim();
            if(!directive) return;

            fetch('/api/directive', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ directive })
            })
            .then(res => res.json())
            .then(() => {
                document.getElementById('directiveInput').value = "";
                loadStats();
            });
        }

        function checkout(tier, price, productName) {
            const email = document.getElementById('customerEmail').value.trim();
            if(!email || !email.includes('@')) {
                alert('Please enter a valid email address first.');
                return;
            }

            fetch('/api/orders/initiate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, tier, price, product_name: productName })
            })
            .then(res => res.json())
            .then(data => {
                if(data.checkout_url) {
                    window.location.href = data.checkout_url;
                } else {
                    window.location.href = "https://www.paypal.com/ncp/payment/WQJ28EPKZHR56";
                }
            });
        }
    </script>
</body>
</html>
"""
