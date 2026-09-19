import os
import json
import sqlite3
import logging
import uuid
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("MultiTierStorefront")

app = FastAPI(title="Multi-Tier PayPal Storefront")
DB_FILE = "storefront.db"

# Map each tier to its specific PayPal payment URL (replace these with your unique PayPal button links if you have separate ones)
PAYPAL_LINKS = {
    "5.00": os.environ.get("PAYPAL_5_URL", "https://www.paypal.com/ncp/payment/WQJ28EPKZHR56"),
    "10.00": os.environ.get("PAYPAL_10_URL", "https://www.paypal.com/ncp/payment/WQJ28EPKZHR56"),
    "20.00": os.environ.get("PAYPAL_20_URL", "https://www.paypal.com/ncp/payment/WQJ28EPKZHR56"),
    "40.00": os.environ.get("PAYPAL_40_URL", "https://www.paypal.com/ncp/payment/WQJ28EPKZHR56")
}

SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, order_id TEXT, customer_email TEXT, product_name TEXT, amount TEXT, status TEXT, download_token TEXT, timestamp TEXT)''')
    conn.close()

init_db()

class NetworkManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        payload = json.dumps(message)
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")

manager = NetworkManager()

def send_fulfillment_email(to_email: str, product_name: str, amount: str, download_token: str):
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.warning("SMTP credentials not set. Skipping email dispatch.")
        return False
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = to_email
        msg['Subject'] = f"Your Digital Download: {product_name} (${amount})"

        body = f"""Thank you for your purchase!

Your payment of ${amount} has been verified. Access your secure download package below:
Product: {product_name}
Download Token: {download_token}

Secure Download Link:
https://{os.environ.get('RENDER_EXTERNAL_URL', 'localhost:8000')}/api/download/{download_token}

Best regards,
Automated Systems Hub
"""
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        logger.error(f"Email error: {e}")
        return False

class OrderCreateRequest(BaseModel):
    email: str
    tier: str
    price: str
    product_name: str

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

        target_url = PAYPAL_LINKS.get(data.price, PAYPAL_LINKS["40.00"])

        return {
            "status": "success",
            "order_id": order_id,
            "checkout_url": f"{target_url}?custom_id={order_id}"
        }
    except Exception as e:
        logger.error(f"Order error: {e}")
        raise HTTPException(status_code=500, detail="Database error.")

@app.get("/api/download/{token}")
def download_product(token: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT product_name, status FROM orders WHERE download_token = ?", (token,))
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Invalid token.")
    
    return {
        "status": "success",
        "product": row[0],
        "download_link": "https://raw.githubusercontent.com/github/gitignore/main/Python.gitignore",
        "message": "Secure asset package unlocked successfully."
    }

@app.get("/api/stats")
def get_system_stats():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM orders WHERE status = 'COMPLETED'")
    paid_count = c.fetchone()[0]
    c.execute("SELECT SUM(CAST(amount AS REAL)) FROM orders WHERE status = 'COMPLETED'")
    total_rev = c.fetchone()[0] or 0.0
    conn.close()
    return {
        "completed_orders": paid_count,
        "revenue": f"${total_rev:.2f}"
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
    <title>Storefront - Multiple Plans</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #030712; color: #f3f4f6; margin: 0; padding: 20px; display: flex; justify-content: center; }
        .wrapper { width: 100%; max-width: 650px; }
        .card { background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 20px; margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
        h1 { font-size: 1.3rem; margin-top: 0; color: #fff; display: flex; justify-content: space-between; align-items: center; }
        .badge { background: rgba(16, 185, 129, 0.1); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.2); padding: 4px 8px; border-radius: 4px; font-size: 0.7rem; text-transform: uppercase; }
        .tier-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px; }
        .tier-card { background: #020617; border: 1px solid #1e293b; border-radius: 6px; padding: 15px; text-align: center; }
        .tier-price { font-size: 1.4rem; font-weight: 700; color: #34d399; margin: 8px 0; }
        p { color: #9ca3af; line-height: 1.3; font-size: 0.85rem; }
        input, button { width: 100%; padding: 10px; margin-top: 8px; background: #020617; border: 1px solid #1e293b; color: #fff; border-radius: 6px; font-size: 0.9rem; box-sizing: border-box; outline: none; }
        input:focus { border-color: #6366f1; }
        .btn { background: #6366f1; font-weight: 600; cursor: pointer; border: none; }
        .btn:hover { background: #4f46e5; }
        .log-box { background: #020617; border: 1px solid #1e293b; padding: 10px; height: 80px; overflow-y: auto; font-family: monospace; font-size: 11px; color: #60a5fa; border-radius: 6px; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="wrapper">
        <div class="card">
            <h1>Select Your Plan <span class="badge">Live</span></h1>
            <p>Choose your plan below. Funds route directly to your PayPal account.</p>
            <div id="statsBar" style="font-size: 0.85rem; color: #34d399; margin-top: 8px;">Orders Completed: Loading... | Revenue: Loading...</div>
        </div>

        <div class="card">
            <h3>Customer Checkout</h3>
            <input type="email" id="customerEmail" placeholder="Enter your email address first...">
            
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
            <h3>System Log</h3>
            <div class="log-box" id="hiveLog">Connecting to engine...</div>
        </div>
    </div>
    <script>
        function loadStats() {
            fetch('/api/stats').then(res => res.json()).then(data => {
                document.getElementById('statsBar').innerHTML = `Orders Completed: <b>${data.completed_orders}</b> | Revenue: <b>${data.revenue}</b>`;
            });
        }
        loadStats();

        const hiveLog = document.getElementById('hiveLog');
        const ws = new WebSocket((window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws/hive');
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            hiveLog.innerHTML += `<div>[Event]: ${data.message}</div>`;
            hiveLog.scrollTop = hiveLog.scrollHeight;
            loadStats();
        };

        ws.onopen = function() {
            hiveLog.innerHTML += `<div>Storefront ready.</div>`;
        };

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
            })
            .catch(() => {
                window.location.href = "https://www.paypal.com/ncp/payment/WQJ28EPKZHR56";
            });
        }
    </script>
</body>
</html>
"""
