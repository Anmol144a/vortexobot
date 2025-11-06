# web.py
# Vortex Dashboard backend
# FastAPI + Jinja2 Templates
# Made by Anmol

import uvicorn
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3
import os
import json
from datetime import datetime

app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# SQLite DB
DB_PATH = os.path.join(BASE_DIR, "vortex.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()
# Create tables if not exist
c.execute("""CREATE TABLE IF NOT EXISTS wallets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    label TEXT,
    address TEXT,
    last_balance TEXT
)""")
c.execute("""CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    txid TEXT,
    address TEXT,
    amount TEXT,
    timestamp TEXT
)""")
conn.commit()

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# API endpoint to receive wallet tx updates from bot
@app.post("/api/tx")
async def receive_tx(data: dict):
    """
    Bot sends:
    {
        "address": "L...",
        "label": "My Wallet",
        "txid": "abc123...",
        "amount": "0.123",
        "timestamp": "2025-11-06T07:00:00"
    }
    """
    try:
        address = data.get("address")
        label = data.get("label")
        txid = data.get("txid")
        amount = data.get("amount")
        ts = data.get("timestamp") or datetime.utcnow().isoformat()
        # Insert into DB
        c.execute("INSERT INTO transactions (txid,address,amount,timestamp) VALUES (?,?,?,?)",
                  (txid, address, amount, ts))
        # Update wallet last_balance
        c.execute("UPDATE wallets SET last_balance=? WHERE address=?", (amount, address))
        conn.commit()
        return JSONResponse({"status": "ok"})
    except Exception as e:
        return JSONResponse({"status": "error", "error": str(e)})

# Dashboard page
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    # Fetch wallets
    c.execute("SELECT user_id,label,address,last_balance FROM wallets")
    wallets = c.fetchall()
    # Fetch last 20 txs
    c.execute("SELECT txid,address,amount,timestamp FROM transactions ORDER BY id DESC LIMIT 20")
    txs = c.fetchall()
    return templates.TemplateResponse("index.html", {"request": request, "wallets": wallets, "txs": txs})

# Endpoint to add wallet (optional admin)
@app.post("/add_wallet")
async def add_wallet(user_id: str = Form(...), label: str = Form(...), address: str = Form(...)):
    try:
        c.execute("INSERT INTO wallets (user_id,label,address,last_balance) VALUES (?,?,?)",
                  (user_id, label, address, "0"))
        conn.commit()
        return JSONResponse({"status": "ok"})
    except Exception as e:
        return JSONResponse({"status": "error", "error": str(e)})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
