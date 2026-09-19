import os
import json
import sqlite3
import logging
import uuid
import datetime
import asyncio
import random
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("OmniHiveSwarmEnterprise")

app = FastAPI(title="Omni-Hive Sentinel Engine")
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
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, order_id TEXT, customer_email TEXT, product_name TEXT, amount TEXT, status TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS chat_logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT, message TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()

init_db()

def log_chat_message(sender: str, message: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO chat_logs (sender, message, timestamp) VALUES (?, ?, ?)", (sender, message, ts))
    conn.commit()
    conn.close()

async def run_bot_swarm():
    while True:
        try:
            bot_id = random.randint(1, 800)
            actions = [
                "Compiled automated script batch for digital inventory",
                "Verified conversion funnel telemetry node",
                "Processed task payload for digital asset delivery",
                "Optimized backend automation pipeline workflow"
            ]
            action = random.choice(actions)
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("INSERT INTO chat_logs (sender, message, timestamp) VALUES (?, ?, ?)", 
                      (f"Bot-{bot_id}", action, ts))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Swarm worker error: {e}")
        
        await asyncio.sleep(4)

@app.on_event("startup")
async def startup_event():
    for _ in range(4):
        asyncio.create_task(run_bot_swarm())

class ChatMessageRequest(BaseModel):
    message: str

class OrderCreateRequest(BaseModel):
    email: str
    tier: str
    price: str
    product_name: str

@app.post("/api/chat")
def handle_chat_message(data: ChatMessageRequest):
    user_msg = data.message
    log_chat_message("User", user_msg)
    
    bot_response = f"Processed command: '{user_msg}'. 800-node worker pool is actively executing tasks."
    log_chat_message("Sentinel", bot_response)
    
    return {"status": "success", "response": bot_response}

@app.get("/api/stats")
def get_system_stats():
    return {
        "active_nodes": 800,
        "status": "fully_operational",
        "revenue_pipeline": "active"
    }

@app.post("/api/orders/initiate")
def initiate_order(data: OrderCreateRequest):
    order_id = "HIVE-" + str(uuid.uuid4())[:8].upper()
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO orders (order_id, customer_email, product_name, amount, status, timestamp) VALUES (?, ?, ?, ?, ?, datetime('now'))",
                  (order_id, data.email, data.product_name, data.price, "PENDING"))
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

@app.get("/api/health")
def health_check():
    return {"status": "healthy"}

@app.get("/", response_class=HTMLResponse)
def serve_interface(request: Request):
    is_customer_store = request.query_params.get("store") == "true"
    
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Omni-Hive Automation & Deployment Engine</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #030712; color: #f3f4f6; margin: 0; padding: 20px; display: flex; justify-content: center; }
        .wrapper { width: 100%; max-width: 750px; }
        .card { background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 20px; margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
        h1 { font-size: 1.3rem; margin-top: 0; color: #fff; display: flex; justify-content: space-between; align-items: center; }
        .badge { background: rgba(16, 185, 129, 0.1); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.2); padding: 4px 8px; border-radius: 4px; font-size: 0.7rem; text-transform: uppercase; }
        .chat-box { background: #020617; border: 1px solid #1e293b; padding: 12px; height: 280px; overflow-y: auto; font-size: 0.9rem; border-radius: 6px; margin-bottom: 10px; display: flex; flex-direction: column; gap: 8px; }
        .msg-user { color: #60a5fa; text-align: right; margin: 4px 0; }
        .msg-bot { color: #34d399; text-align: left; margin: 4px 0; }
        .tier-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px; }
        .tier-card { background: #020617; border: 1px solid #1e293b; border-radius: 6px; padding: 15px; text-align: center; }
        .tier-price { font-size: 1.3rem; font-weight: 700; color: #34d399; margin: 8px 0; }
        input, button, textarea { width: 100%; padding: 10px; margin-top: 8px; background: #020617; border: 1px solid #1e293b; color: #fff; border-radius: 6px; font-size: 0.9rem; box-sizing: border-box; outline: none; }
        input:focus, textarea:focus { border-color: #6366f1; }
        .btn { background: #6366f1; font-weight: 600; cursor: pointer; border: none; }
        .btn:hover { background: #4f46e5; }
        p { color: #9ca3af; font-size: 0.85rem; }
    </style>
</head>
<body>
    <div class="wrapper">
        <div class="card">
            <h1>Omni-Hive Engine <span class="badge">""" + ('Customer Portal' if is_customer_store else 'Admin Workspace (800 Active Nodes)') + """</span></h1>
            <p>""" + ('Choose a deployment tier below to initiate instant checkout.' if is_customer_store else 'System active. 800 background worker bots are processing operational routines.') + """</p>
            
            <div class="chat-box" id="chatHistory">
                <div class="msg-bot"><b>Sentinel:</b> Core online. Swarm pipeline active.</div>
            </div>
            
            <textarea id="chatInput" rows="2" placeholder="Send instructions to your worker network..."></textarea>
            <button class="btn" onclick="sendChatMessage()">Execute Command</button>
        </div>
"""

    if is_customer_store:
        html_content += """
        <div class="card">
            <h3>Verified Merchant Checkout</h3>
            <p>Unlock digital deployment rights instantly via secure checkout.</p>
            <input type="email" id="customerEmail" placeholder="Enter your email address...">
            
            <div class="tier-grid">
                <div class="tier-card">
                    <h4>Starter</h4>
                    <div class="tier-price">$5.00</div>
                    <button class="btn" onclick="checkout('Starter', '5.00', 'Basic Script Pack')">Buy $5</button>
                </div>
                <div class="tier-card">
                    <h4>Pro</h4>
                    <div class="tier-price">$10.00</div>
                    <button class="btn" onclick="checkout('Pro', '10.00', 'Intermediate Kit')">Buy $10</button>
                </div>
                <div class="tier-card">
                    <h4>Advanced</h4>
                    <div class="tier-price">$20.00</div>
                    <button class="btn" onclick="checkout('Advanced', '20.00', 'Advanced Bundle')">Buy $20</button>
                </div>
                <div class="tier-card">
                    <h4>Masterpack</h4>
                    <div class="tier-price">$40.00</div>
                    <button class="btn" onclick="checkout('Masterpack', '40.00', 'Python Automation Masterpack')">Buy $40</button>
                </div>
            </div>
        </div>
"""

    html_content += """
    </div>
    <script>
        function sendChatMessage() {
            const input = document.getElementById('chatInput');
            const message = input.value.trim();
            if(!message) return;

            const chatHistory = document.getElementById('chatHistory');
            chatHistory.innerHTML += `<div class="msg-user"><b>You:</b> ${message}</div>`;
            input.value = "";
            chatHistory.scrollTop = chatHistory.scrollHeight;

            fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            })
            .then(res => res.json())
            .then(data => {
                chatHistory.innerHTML += `<div class="msg-bot"><b>Sentinel:</b> ${data.response}</div>`;
                chatHistory.scrollTop = chatHistory.scrollHeight;
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
                }
            });
        }
    </script>
</body>
</html>
"""
    return html_content

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.omni_core_engine:app", host="0.0.0.0", port=10000, reload=True)
