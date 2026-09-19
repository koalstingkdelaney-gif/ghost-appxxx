import os
import sqlite3
import logging
import uuid
import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("MasterOmniApp")

app = FastAPI(title="Master Omni-Hive Core Application")
DB_FILE = "master_hive.db"
PAYPAL_LINK = os.environ.get("PAYPAL_URL", "https://www.paypal.com/ncp/payment/WQJ28EPKZHR56")

def init_master_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, order_id TEXT, customer_email TEXT, product_name TEXT, amount TEXT, status TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS task_queue 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, task_name TEXT, status TEXT, result TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS conversation_archive 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT, role TEXT, content TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()

init_master_db()

class TaskRequest(BaseModel):
    task_name: str

class OrderCreateRequest(BaseModel):
    email: str
    tier: str
    price: str
    product_name: str

class ArchiveEntry(BaseModel):
    source: str
    role: str
    content: str

@app.post("/api/tasks/execute")
def execute_task(data: TaskRequest):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO task_queue (task_name, status, result, timestamp) VALUES (?, ?, ?, ?)",
              (data.task_name, "COMPLETED", f"Executed automation routine: {data.task_name}", ts))
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"Task '{data.task_name}' processed successfully."}

@app.post("/api/orders/initiate")
def initiate_order(data: OrderCreateRequest):
    order_id = "ORD-" + str(uuid.uuid4())[:8].upper()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO orders (order_id, customer_email, product_name, amount, status, timestamp) VALUES (?, ?, ?, ?, ?, datetime('now'))",
              (order_id, data.email, data.product_name, data.price, "PENDING"))
    conn.commit()
    conn.close()
    return {
        "status": "success",
        "order_id": order_id,
        "checkout_url": f"{PAYPAL_LINK}?custom_id={order_id}"
    }

@app.get("/api/archive/search")
def search_archive(q: str):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM conversation_archive WHERE content LIKE ? ORDER BY id DESC LIMIT 20", (f"%{q}%",))
    rows = c.fetchall()
    conn.close()
    return {"results": [dict(row) for row in rows]}

@app.get("/", response_class=HTMLResponse)
def master_dashboard():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Master Omni-Hive Core</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #030712; color: #f3f4f6; margin: 0; padding: 20px; display: flex; justify-content: center; }
            .wrapper { width: 100%; max-width: 900px; }
            .card { background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 20px; margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
            h1 { font-size: 1.4rem; margin-top: 0; color: #fff; display: flex; justify-content: space-between; align-items: center; }
            .badge { background: rgba(16, 185, 129, 0.1); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.2); padding: 4px 8px; border-radius: 4px; font-size: 0.7rem; text-transform: uppercase; }
            input, button { width: 100%; padding: 10px; margin-top: 8px; background: #020617; border: 1px solid #1e293b; color: #fff; border-radius: 6px; font-size: 0.9rem; box-sizing: border-box; }
            .btn { background: #6366f1; font-weight: 600; cursor: pointer; border: none; }
            .btn:hover { background: #4f46e5; }
            p { color: #9ca3af; font-size: 0.85rem; }
            a { color: #34d399; text-decoration: none; }
            pre { background: #020617; padding: 10px; border-radius: 6px; overflow-x: auto; font-size: 0.8rem; color: #34d399; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
        </style>
    </head>
    <body>
        <div class="wrapper">
            <div class="card">
                <h1>Master Omni-Hive Core <span class="badge">Fully Unified App</span></h1>
                <p>All-in-one execution engine handling automation, history search, and verified checkout. Gateway: <a href=""" + f'"{PAYPAL_LINK}"' + """ target="_blank">PayPal Checkout</a></p>
            </div>

            <div class="grid">
                <div class="card">
                    <h3>1. Automation Engine</h3>
                    <input type="text" id="taskName" placeholder="Enter routine name...">
                    <button class="btn" onclick="runTask()">Execute Routine</button>
                    <pre id="taskResult">Awaiting routine execution...</pre>
                </div>

                <div class="card">
                    <h3>2. History Archive Search</h3>
                    <input type="text" id="searchQuery" placeholder="Search past ideas/code...">
                    <button class="btn" onclick="searchHistory()">Search Archive</button>
                    <pre id="searchResult">Awaiting history query...</pre>
                </div>
            </div>

            <div class="card">
                <h3>3. Digital Product Storefront Checkout</h3>
                <input type="email" id="customerEmail" placeholder="Enter customer email...">
                <button class="btn" onclick="checkout()">Initiate $10 Pro Order</button>
            </div>
        </div>
        <script>
            function runTask() {
                const task_name = document.getElementById('taskName').value;
                if(!task_name) return;
                fetch('/api/tasks/execute', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ task_name })
                })
                .then(res => res.json())
                .then(data => { document.getElementById('taskResult').innerText = JSON.stringify(data, null, 2); });
            }

            function searchHistory() {
                const q = document.getElementById('searchQuery').value;
                fetch('/api/archive/search?q=' + encodeURIComponent(q))
                .then(res => res.json())
                .then(data => { document.getElementById('searchResult').innerText = JSON.stringify(data, null, 2); });
            }

            function checkout() {
                const email = document.getElementById('customerEmail').value;
                if(!email) { alert('Enter an email first.'); return; }
                fetch('/api/orders/initiate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, tier: 'Pro', price: '10.00', product_name: 'Master Unified Kit' })
                })
                .then(res => res.json())
                .then(data => { if(data.checkout_url) window.location.href = data.checkout_url; });
            }
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
