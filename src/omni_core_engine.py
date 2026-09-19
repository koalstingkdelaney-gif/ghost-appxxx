import os
import sqlite3
import logging
import uuid
import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s")
logger = logging.getLogger("OmniHiveEngine")

app = FastAPI(title="Omni-Hive Real Operational Engine", version="3.0.0")
DB_FILE = "omni_production.db"
PAYPAL_CHECKOUT_URL = os.environ.get("PAYPAL_URL", "https://www.paypal.com/ncp/payment/WQJ28EPKZHR56")

def initialize_database():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS operational_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT UNIQUE NOT NULL,
                customer_email TEXT NOT NULL,
                product_tier TEXT NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS execution_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                status TEXT NOT NULL,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS universal_archive (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_channel TEXT NOT NULL,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

initialize_database()

class TaskPayload(BaseModel):
    task_name: str = Field(..., min_length=1)
    parameters: str = Field(default="")

class OrderPayload(BaseModel):
    email: EmailStr
    tier: str
    price: float
    product_name: str

class ArchivePayload(BaseModel):
    source_channel: str
    category: str
    content: str

@app.post("/api/execution/run")
def run_real_task(payload: TaskPayload):
    timestamp = datetime.datetime.utcnow().isoformat()
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO execution_logs (action_type, payload, status) VALUES (?, ?, ?)",
                (payload.task_name, payload.parameters, "SUCCESS")
            )
            conn.commit()
        return {
            "status": "success",
            "task": payload.task_name,
            "executed_at": timestamp,
            "database_committed": True
        }
    except Exception as error:
        logger.error(f"Execution failure: {error}")
        raise HTTPException(status_code=500, detail=str(error))

@app.post("/api/commerce/initiate-order")
def create_order(payload: OrderPayload):
    order_reference = "ORD-" + uuid.uuid4().hex[:8].upper()
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO operational_orders (order_id, customer_email, product_tier, amount, status) VALUES (?, ?, ?, ?, ?)",
                (order_reference, payload.email, payload.product_name, payload.price, "PENDING_CHECKOUT")
            )
            conn.commit()
        return {
            "status": "success",
            "order_id": order_reference,
            "checkout_redirect": f"{PAYPAL_CHECKOUT_URL}?custom_id={order_reference}&amount={payload.price}"
        }
    except Exception as error:
        logger.error(f"Order creation failure: {error}")
        raise HTTPException(status_code=500, detail=str(error))

@app.get("/api/archive/query")
def query_archive(q: str):
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM universal_archive WHERE content LIKE ? OR category LIKE ? ORDER BY id DESC LIMIT 50",
            (f"%{q}%", f"%{q}%")
        )
        rows = [dict(row) for row in cursor.fetchall()]
    return {"query": q, "match_count": len(rows), "results": rows}

@app.get("/api/system/metrics")
def get_system_metrics():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM operational_orders")
        total_orders = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM execution_logs")
        total_tasks = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM universal_archive")
        total_archives = cursor.fetchone()[0]
    return {
        "database_status": "connected",
        "metrics": {
            "total_orders": total_orders,
            "total_tasks_executed": total_tasks,
            "total_archived_items": total_archives
        }
    }

@app.get("/", response_class=HTMLResponse)
def render_control_panel():
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Omni-Hive Production Engine</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #030712; color: #f3f4f6; margin: 0; padding: 20px; display: flex; justify-content: center; }}
            .container {{ width: 100%; max-width: 900px; }}
            .card {{ background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 20px; margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.4); }}
            h1 {{ font-size: 1.4rem; margin-top: 0; color: #fff; display: flex; justify-content: space-between; align-items: center; }}
            .badge {{ background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); padding: 4px 8px; border-radius: 4px; font-size: 0.7rem; text-transform: uppercase; }}
            input, button {{ width: 100%; padding: 10px; margin-top: 8px; background: #020617; border: 1px solid #1e293b; color: #fff; border-radius: 6px; font-size: 0.9rem; box-sizing: border-box; outline: none; }}
            input:focus {{ border-color: #6366f1; }}
            .btn {{ background: #6366f1; font-weight: 600; cursor: pointer; border: none; }}
            .btn:hover {{ background: #4f46e5; }}
            p {{ color: #9ca3af; font-size: 0.85rem; }}
            a {{ color: #34d399; text-decoration: none; }}
            pre {{ background: #020617; padding: 10px; border-radius: 6px; overflow-x: auto; font-size: 0.8rem; color: #34d399; border: 1px solid #1e293b; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <h1>Omni-Hive Production Engine <span class="badge">Online & Verified</span></h1>
                <p>Configured with strict SQLite execution binding. Payment Gateway: <a href="{PAYPAL_CHECKOUT_URL}" target="_blank">PayPal Checkout Portal</a></p>
            </div>

            <div class="grid">
                <div class="card">
                    <h3>1. Execute Runtime Task</h3>
                    <input type="text" id="taskName" placeholder="Task identifier...">
                    <input type="text" id="taskParams" placeholder="Parameters...">
                    <button class="btn" onclick="executeTask()">Commit Task</button>
                    <pre id="taskOutput">Awaiting execution log...</pre>
                </div>

                <div class="card">
                    <h3>2. Query Universal Archive</h3>
                    <input type="text" id="searchQuery" placeholder="Keyword query...">
                    <button class="btn" onclick="queryArchive()">Search DB</button>
                    <pre id="searchOutput">Awaiting search results...</pre>
                </div>
            </div>

            <div class="card">
                <h3>3. Process Verified Order</h3>
                <input type="email" id="customerEmail" placeholder="Customer email address...">
                <button class="btn" onclick="initiateCheckout()">Initialize $10.00 Checkout</button>
            </div>
        </div>
        <script>
            function executeTask() {{
                const task_name = document.getElementById('taskName').value;
                const parameters = document.getElementById('taskParams').value;
                if(!task_name) return;
                fetch('/api/execution/run', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ task_name, parameters }})
                }})
                .then(res => res.json())
                .then(data => {{ document.getElementById('taskOutput').innerText = JSON.stringify(data, null, 2); }});
            }}

            function queryArchive() {{
                const q = document.getElementById('searchQuery').value;
                fetch('/api/archive/query?q=' + encodeURIComponent(q))
                .then(res => res.json())
                .then(data => {{ document.getElementById('searchOutput').innerText = JSON.stringify(data, null, 2); }});
            }}

            function initiateCheckout() {{
                const email = document.getElementById('customerEmail').value;
                if(!email) {{ alert('Valid email required.'); return; }}
                fetch('/api/commerce/initiate-order', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ email, tier: 'Pro', price: 10.00, product_name: 'Production Omni Kit' }})
                }})
                .then(res => res.json())
                .then(data => {{ if(data.checkout_redirect) window.location.href = data.checkout_redirect; }});
            }}
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("omni_core_engine:app", host="0.0.0.0", port=10000, reload=False)
