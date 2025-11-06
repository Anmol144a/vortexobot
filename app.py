# app.py
# Vortex Dashboard - FastAPI + Supabase (Serverless-ready)
# Made by Anmol

import psycopg2
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory=".")

# -----------------------------
# Supabase connection string
# -----------------------------
DB_URL = "postgresql://postgres:REDHAT#1@db.enciwuvvqhnkkfourhkm.supabase.co:5432/postgres"

# -----------------------------
# Helper: get new connection and cursor per request
# -----------------------------
def get_cursor():
    conn = psycopg2.connect(DB_URL)
    return conn, conn.cursor()

# -----------------------------
# Dashboard page
# -----------------------------
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    conn, c = get_cursor()
    c.execute("SELECT user_id,label,address,last_balance FROM wallets")
    wallets = c.fetchall()
    c.execute("SELECT txid,address,amount,timestamp FROM transactions ORDER BY id DESC LIMIT 20")
    txs = c.fetchall()
    conn.close()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "wallets": wallets, "txs": txs}
    )

# -----------------------------
# API endpoint for bot transactions
# -----------------------------
@app.post("/api/tx")
async def receive_tx(data: dict):
    try:
        conn, c = get_cursor()
        address = data.get("address")
        label = data.get("label") or "unknown"
        txid = data.get("txid")
        amount = data.get("amount")
        ts = data.get("timestamp") or datetime.utcnow()

        # Insert transaction
        c.execute(
            "INSERT INTO transactions (txid,address,amount,timestamp) VALUES (%s,%s,%s,%s)",
            (txid, address, amount, ts)
        )

        # Update wallet last_balance or insert new wallet
        c.execute("SELECT id FROM wallets WHERE address=%s", (address,))
        if c.fetchone():
            c.execute("UPDATE wallets SET last_balance=%s WHERE address=%s", (amount, address))
        else:
            c.execute(
                "INSERT INTO wallets (user_id,label,address,last_balance) VALUES (%s,%s,%s,%s)",
                ("unknown", label, address, amount)
            )

        conn.commit()
        conn.close()
        return JSONResponse({"status": "ok"})
    except Exception as e:
        return JSONResponse({"status": "error", "error": str(e)})

# -----------------------------
# Add wallet manually
# -----------------------------
@app.post("/add_wallet")
async def add_wallet(user_id: str = Form(...), label: str = Form(...), address: str = Form(...)):
    try:
        conn, c = get_cursor()
        c.execute(
            "INSERT INTO wallets (user_id,label,address,last_balance) VALUES (%s,%s,%s,%s)",
            (user_id, label, address, "0")
        )
        conn.commit()
        conn.close()
        return JSONResponse({"status": "ok"})
    except Exception as e:
        return JSONResponse({"status": "error", "error": str(e)})

# -----------------------------
# Run locally
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
