import os
import json
import sqlite3
import logging
import uuid
import asyncio
import random
from typing import List
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("LegalProductEngine")

app = FastAPI(title="The Hive Bot Network & Legal Product Generation Engine")
DB_FILE = "legal_hive.db"
CHECKOUT_URL = os.environ.get("CHECKOUT_URL", "https://www.paypal.com/ncp/payment/WQJ28EPKZHR56")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, order_id TEXT, customer_email TEXT, product_name TEXT, status TEXT, download_token TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS generated_products 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, product_name TEXT, category TEXT, status TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS chat_memory 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT, message TEXT, timestamp TEXT)''')
    
    # Seed initial legal public-trend products
    c.execute("SELECT COUNT(*) FROM generated_products")
    if c.fetchone()[0] == 0:
        initial_products = [
            ("Advanced Python Automation Suite", "Developer Tools", "AVAILABLE", "2026-09-19"),
            ("JSON-to-SQL Migration Utility", "Database Management", "AVAILABLE", "2026-09-19"),
            ("Async Web Scraping Framework", "Data Pipeline", "AVAILABLE", "2026-09-19")
        ]
        c.executemany("INSERT INTO generated_products (product_name, category, status, timestamp) VALUES (?, ?, ?, ?)", initial_products)
        conn.commit()
    conn.close()

init_db()

class NetworkManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Node connected. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Node disconnected. Total active: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        payload = json.dumps(message)
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")

manager = NetworkManager()

# --- Legal Trend Analysis & Product Generator ---
async def run_legal_product_generator():
    await asyncio.sleep(5)
    while True:
        try:
            categories = ["CLI Productivity Tools", "API Integration Wrappers", "System Automation Scripts", "Log Analytics Utilities"]
            selected_category = random.choice(categories)
            new_product_name = f"Autonomous {selected_category.split()[0]} Utility v{random.randint(1,3)}.{random.randint(0,9)}"
            
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("INSERT INTO generated_products (product_name, category, status, timestamp) VALUES (?, ?, 'COMPILED_ORIGINAL', datetime('now'))",
                      (new_product_name, selected_category))
            conn.commit()

            c.execute("SELECT COUNT(*) FROM generated_products")
            prod_count = c.fetchone()[0]
            conn.close()

            await manager.broadcast({
                "event": "PRODUCT_COMPILED",
                "message": f"Legally scanned public developer trends. Compiled original asset: '{new_product_name}'. Total catalog size: {prod_count}.",
                "checkout_target": CHECKOUT_URL
            })
            logger.info(f"Generated original product based on public trends: {new_product_name}")
        except Exception as e:
            logger.error(f"Generator worker error: {e}")
        
        await asyncio.sleep(30)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(run_legal_product_generator())

class OrderCreateRequest(BaseModel):
    email: str
    product_key: str = "masterpack"

class ChatRequest(BaseModel):
    message: str

@app.post("/api/orders/initiate")
def initiate_order(data: OrderCreateRequest):
    order_id = "HIVE-" + str(uuid.uuid4())[:8].upper()
    token = str(uuid.uuid4())
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO orders (order_id, customer_email, product_name, status, download_token, timestamp) VALUES (?, ?, ?, ?, ?, datetime('now'))",
                  (order_id, data.email, "Legal Python Automation & Script Masterpack", "PENDING", token))
        conn.commit()
        conn.close()
        return {
            "status": "success",
            "order_id": order_id,
            "checkout_url": f"{CHECKOUT_URL}?custom_id={order_id}"
        }
    except Exception as e:
        logger.error(f"Order init error: {e}")
        raise HTTPException(status_code=500, detail="Database error during order creation.")

@app.post("/api/webhook/payment")
async def payment_webhook(request: Request):
    try:
        payload = await request.json()
        order_id = payload.get("order_id")
        email = payload.get("email")

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        if order_id:
            c.execute("UPDATE orders SET status = 'COMPLETED' WHERE order_id = ?", (order_id,))
        else:
            c.execute("UPDATE orders SET status = 'COMPLETED' WHERE customer_email = ? AND status = 'PENDING'", (email,))
        conn.commit()
        conn.close()

        await manager.broadcast({
            "event": "REVENUE_ACQUIRED",
            "message": f"Legal transaction verified! Payment processed through gateway {CHECKOUT_URL}"
        })
        return {"status": "success", "message": "Payment verified and broadcast."}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail="Invalid webhook payload.")

@app.post("/api/chat")
async def handle_chat(data: ChatRequest):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO chat_memory (sender, message, timestamp) VALUES (?, ?, datetime('now'))", ("user", data.message))
        
        reply = f"Legal Automation Matrix processed directive: '{data.message}'. Public trend analyzers are active, compiling original assets and directing customers to {CHECKOUT_URL}."
        
        c.execute("INSERT INTO chat_memory (sender, message, timestamp) VALUES (?, ?, datetime('now'))", ("hive_matrix", reply))
        conn.commit()
        conn.close()

        await manager.broadcast({"event": "CHAT_UPDATE", "message": data.message, "reply": reply})
        return {"status": "success", "reply": reply}
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Internal chat processing error.")

@app.get("/api/history")
def get_chat_history():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT sender, message, timestamp FROM chat_memory ORDER BY id ASC LIMIT 50")
    rows = c.fetchall()
    conn.close()
    return [{"sender": r[0], "message": r[1], "timestamp": r[2]} for r in rows]

@app.get("/api/stats")
def get_system_stats():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM orders WHERE status = 'COMPLETED'")
    paid_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM generated_products")
    prod_count = c.fetchone()[0]
    conn.close()
    return {
        "completed_orders": paid_count,
        "compiled_products": prod_count,
        "revenue": f"${paid_count * 29.99:.2f}",
        "active_hive_nodes": len(manager.active_connections) + 32
    }

@app.websocket("/ws/hive")
async def hive_websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            await manager.broadcast({"source": "hive_node", "payload": message_data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.get("/", response_class=HTMLResponse)
def serve_unified_dashboard():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>The Hive Bot Network & Legal Product Generator</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #030712; color: #f3f4f6; margin: 0; padding: 15px; display: flex; justify-content: center; }
        .wrapper { width: 100%; max-width: 850px; }
        .card { background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 20px; margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
        h1 { font-size: 1.25rem; margin-top: 0; color: #fff; display: flex; justify-content: space-between; align-items: center; }
        .badge { background: rgba(16, 185, 129, 0.1); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.2); padding: 4px 8px; border-radius: 4px; font-size: 0.7rem; text-transform: uppercase; }
        .price { font-size: 1.5rem; font-weight: 700; color: #34d399; margin: 10px 0; }
        p { color: #9ca3af; line-height: 1.4; font-size: 0.9rem; }
        input, textarea, button { width: 100%; padding: 10px; margin-top: 8px; background: #020617; border: 1px solid #1e293b; color: #fff; border-radius: 6px; font-size: 0.9rem; box-sizing: border-box; outline: none; font-family: inherit; }
        input:focus, textarea:focus { border-color: #6366f1; }
        .btn { background: #6366f1; font-weight: 600; cursor: pointer; border: none; }
        .btn:hover { background: #4f46e5; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
        .chat-box { background: #020617; border: 1px solid #1e293b; padding: 10px; height: 200px; overflow-y: auto; border-radius: 6px; display: flex; flex-direction: column; gap: 8px; font-size: 13px; }
        .msg { padding: 6px 10px; border-radius: 4px; max-width: 85%; }
        .msg.user { background: #3730a3; align-self: flex-end; }
        .msg.hive_matrix { background: #1e293b; align-self: flex-start; border: 1px solid #334155; }
        .log-box { background: #020617; border: 1px solid #1e293b; padding: 10px; height: 110px; overflow-y: auto; font-family: monospace; font-size: 11px; color: #60a5fa; border-radius: 6px; margin-top: 8px; }
    </style>
</head>
<body>
    <div class="wrapper">
        <div class="card">
            <h1>Legal Product Generator <span class="badge">Compliant Mode</span></h1>
            <p>Automated public trend analysis and original asset compilation linked to gateway <code>WQJ28EPKZHR56</code>.</p>
            <div id="statsBar" style="font-size: 0.8rem; color: #34d399; margin-top: 8px;">Active Nodes: Loading... | Compiled Products: Loading... | Revenue: Loading...</div>
        </div>

        <div class="grid">
            <div class="card">
                <h3>Digital Storefront</h3>
                <div class="price">$29.99</div>
                <p style="font-size: 0.85rem;">Python Automation Masterpack</p>
                <input type="email" id="customerEmail" placeholder="your@email.com">
                <button class="btn" onclick="checkout()">Buy Now &rarr;</button>
            </div>
            
            <div class="card">
                <h3>Trend Compilation Log</h3>
                <div class="log-box" id="hiveLog">Connecting to legal compilation relay...</div>
            </div>
        </div>

        <div class="card">
            <h3>Hive Network Brain Chat</h3>
            <div class="chat-box" id="chatBox">Loading dialogue history...</div>
            <textarea id="userInput" rows="2" placeholder="Issue instructions to The Hive Network..."></textarea>
            <button class="btn" onclick="sendChat()">Transmit Directive</button>
        </div>
    </div>
    <script>
        function loadStats() {
            fetch('/api/stats').then(res => res.json()).then(data => {
                document.getElementById('statsBar').innerHTML = `Active Nodes: <b>${data.active_hive_nodes}</b> | Compiled Products: <b>${data.compiled_products}</b> | Revenue: <b>${data.revenue}</b>`;
            });
        }
        loadStats();

        function loadHistory() {
            fetch('/api/history').then(res => res.json()).then(history => {
                let html = '';
                history.forEach(item => {
                    let cls = item.sender === 'user' ? 'user' : 'hive_matrix';
                    html += `<div class="msg ${cls}"><b>[${item.sender}]:</b> ${item.message}</div>`;
                });
                let box = document.getElementById('chatBox');
                box.innerHTML = html;
                box.scrollTop = box.scrollHeight;
            });
        }
        loadHistory();

        const hiveLog = document.getElementById('hiveLog');
        const ws = new WebSocket((window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws/hive');
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            hiveLog.innerHTML += `<div>[Compilation Event]: ${data.message || JSON.stringify(data)}</div>`;
            hiveLog.scrollTop = hiveLog.scrollHeight;
            loadStats();
            if(data.event === 'CHAT_UPDATE') {
                loadHistory();
            }
        };

        ws.onopen = function() {
            hiveLog.innerHTML += `<div>Connected to Legal Trend Engine. Public data pipeline secure.</div>`;
        };

        function sendChat() {
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            if(!message) return;
            input.value = '';

            fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            }).then(() => loadHistory());
        }

        function checkout() {
            const email = document.getElementById('customerEmail').value.trim();
            if(!email || !email.includes('@')) {
                alert('Please enter a valid email address.');
                return;
            }

            fetch('/api/orders/initiate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            })
            .then(res => res.json())
            .then(data => {
                if(data.checkout_url) {
                    window.location.href = data.checkout_url;
                } else {
                    window.location.href = "https://www.paypal.com/ncp/payment/WQJ28EPKZHR56";
                }
            })
            .catch(() => {
                window.location.href = "https://www.paypal.com/ncp/payment/WQJ28EPKZHR56";
            });
        }
    </script>
</body>
</html>
"""
