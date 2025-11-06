# Vortex Dashboard backend - single folder setup
# FastAPI + Jinja2 Templates
# Made by Anmol

import uvicorn
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import sqlite3
from datetime import datetime

app = FastAPI()

# SQLite DB in root
DB_PATH = "vortex.db"
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

# Templates in root
templates = Jinja2Templates(directory=".")

# API endpoint to receive wallet tx updates from bot
@app.post("/api/tx")
async def receive_tx(data: dict):
    try:
        address = data.get("address")
        label = data.get("label")
        txid = data.get("txid")
        amount = data.get("amount")
        ts = data.get("timestamp") or datetime.utcnow().isoformat()

        # Insert transaction
        c.execute("INSERT INTO transactions (txid,address,amount,timestamp) VALUES (?,?,?,?)",
                  (txid, address, amount, ts))

        # Update wallet last_balance
        c.execute("UPDATE wallets SET last_balance=? WHERE address=?", (amount, address))
        conn.commit()
        return JSONResponse({"status": "ok"})
    except Exception as e:
        return JSONResponse({"status": "error", "error": str(e)})

# Dashboard
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    c.execute("SELECT user_id,label,address,last_balance FROM wallets")
    wallets = c.fetchall()
    c.execute("SELECT txid,address,amount,timestamp FROM transactions ORDER BY id DESC LIMIT 20")
    txs = c.fetchall()
    return templates.TemplateResponse("index.html", {"request": request, "wallets": wallets, "txs": txs})

# Add wallet (optional)
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
