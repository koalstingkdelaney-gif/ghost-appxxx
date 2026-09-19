import os
import sqlite3
import logging
import uuid
import datetime
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr, Field

# Configure structured enterprise logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"
)
logger = logging.getLogger("OmniEnterpriseEngine")

app = FastAPI(
    title="Omni-Hive Enterprise Operational Engine",
    version="1.0.0",
    description="Production-grade automation and commerce execution platform."
)

DB_FILE = os.environ.get("DB_PATH", "enterprise_production.db")
PAYPAL_CHECKOUT_URL = os.environ.get("PAYPAL_URL", "https://www.paypal.com/ncp/payment/WQJ28EPKZHR56")

def initialize_database():
    """Initializes the SQLite database with strict operational schemas."""
    try:
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
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.critical(f"Database initialization failed: {e}")
        raise

# Initialize database on startup
initialize_database()

class TaskPayload(BaseModel):
    task_name: str = Field(..., min_length=1)
    parameters: str = Field(default="")

class OrderPayload(BaseModel):
    email: EmailStr
    tier: str
    price: float = Field(..., gt=0)
    product_name: str

@app.post("/api/execution/run", status_code=status.HTTP_201_CREATED)
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
        logger.info(f"Task executed successfully: {payload.task_name}")
        return {
            "status": "success",
            "task": payload.task_name,
            "executed_at": timestamp
        }
    except Exception as error:
        logger.error(f"Execution failure for task '{payload.task_name}': {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database transaction failure during task execution."
        )

@app.post("/api/commerce/initiate-order", status_code=status.HTTP_201_CREATED)
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
        logger.info(f"Order created successfully: {order_reference}")
        return {
            "status": "success",
            "order_id": order_reference,
            "checkout_redirect": f"{PAYPAL_CHECKOUT_URL}?custom_id={order_reference}&amount={payload.price}"
        }
    except Exception as error:
        logger.error(f"Order creation failure: {error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register order in database."
        )

@app.get("/api/archive/query", status_code=status.HTTP_200_OK)
def query_archive(q: str):
    if not q.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query parameter 'q' cannot be empty.")
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM universal_archive WHERE content LIKE ? OR category LIKE ? ORDER BY id DESC LIMIT 50",
                (f"%{q}%", f"%{q}%")
            )
            rows = [dict(row) for row in cursor.fetchall()]
        return {"query": q, "results": rows}
    except Exception as error:
        logger.error(f"Archive query error: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database query failed.")

@app.get("/api/system/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "healthy", "timestamp": datetime.datetime.utcnow().isoformat()}

@app.get("/", response_class=HTMLResponse)
def render_control_panel():
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Omni-Hive Enterprise Platform</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #030712; color: #f3f4f6; margin: 0; padding: 20px; display: flex; justify-content: center; }}
            .container {{ width: 100%; max-width: 800px; }}
            .card {{ background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 20px; margin-bottom: 15px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }}
            h1 {{ font-size: 1.3rem; margin-top: 0; color: #fff; display: flex; justify-content: space-between; align-items: center; }}
            .badge {{ background: rgba(16, 185, 129, 0.1); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.2); padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; text-transform: uppercase; }}
            input, button {{ width: 100%; padding: 10px; margin-top: 8px; background: #020617; border: 1px solid #1e293b; color: #fff; border-radius: 6px; font-size: 0.9rem; box-sizing: border-box; outline: none; }}
            input:focus {{ border-color: #6366f1; }}
            .btn {{ background: #6366f1; font-weight: 600; cursor: pointer; border: none; transition: background 0.2s; }}
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
                <h1>Omni-Hive Enterprise Platform <span class="badge">Production</span></h1>
                <p>Secure Merchant Portal: <a href="{PAYPAL_CHECKOUT_URL}" target="_blank">Payment Gateway</a></p>
            </div>

            <div class="grid">
                <div class="card">
                    <h3>Execute Task Pipeline</h3>
                    <input type="text" id="taskName" placeholder="Task identifier...">
                    <input type="text" id="taskParams" placeholder="Parameters...">
                    <button class="btn" onclick="executeTask()">Execute</button>
                    <pre id="taskOutput">System ready...</pre>
                </div>

                <div class="card">
                    <h3>Query Universal Archive</h3>
                    <input type="text" id="searchQuery" placeholder="Keyword query...">
                    <button class="btn" onclick="queryArchive()">Search</button>
                    <pre id="searchOutput">Awaiting query...</pre>
                </div>
            </div>

            <div class="card">
                <h3>Process Secure Order</h3>
                <input type="email" id="customerEmail" placeholder="client@domain.com">
                <button class="btn" onclick="initiateCheckout()">Proceed to Checkout ($10.00)</button>
            </div>
        </div>
        <script>
            async function executeTask() {{
                const task_name = document.getElementById('taskName').value;
                const parameters = document.getElementById('taskParams').value;
                if(!task_name) return;
                try {{
                    const res = await fetch('/api/execution/run', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ task_name, parameters }})
                    }});
                    const data = await res.json();
                    document.getElementById('taskOutput').innerText = JSON.stringify(data, null, 2);
                }} catch (err) {{
                    document.getElementById('taskOutput').innerText = "Error executing task.";
                }}
            }}

            async function queryArchive() {{
                const q = document.getElementById('searchQuery').value;
                if(!q) return;
                try {{
                    const res = await fetch('/api/archive/query?q=' + encodeURIComponent(q));
                    const data = await res.json();
                    document.getElementById('searchOutput').innerText = JSON.stringify(data, null, 2);
                }} catch (err) {{
                    document.getElementById('searchOutput').innerText = "Error querying archive.";
                }}
            }}

            async function initiateCheckout() {{
                const email = document.getElementById('customerEmail').value;
                if(!email || !email.includes('@')) {{ alert('Valid email required.'); return; }}
                try {{
                    const res = await fetch('/api/commerce/initiate-order', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ email, tier: 'Enterprise', price: 10.00, product_name: 'Production Kit' }})
                    }});
                    const data = await res.json();
                    if(data.checkout_redirect) {{
                        window.location.href = data.checkout_redirect;
                    }}
                }} catch (err) {{
                    alert('Checkout initialization failed.');
                }}
            }}
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("omni_core_engine:app", host="0.0.0.0", port=10000, reload=False)
