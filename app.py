# Vortex Dashboard - JSON DB for Vercel
# FastAPI + Jinja2 Templates
# Made by Anmol

import uvicorn
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import json
from datetime import datetime
import os

app = FastAPI()
templates = Jinja2Templates(directory=".")

# JSON database path in root
DB_FILE = "db.json"

# Initialize JSON file if it doesn't exist
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump({"wallets": [], "transactions": []}, f)

# Helper functions
def read_db():
    with open(DB_FILE, "r") as f:
        return json.load(f)

def write_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

# API endpoint to receive wallet tx updates from bot
@app.post("/api/tx")
async def receive_tx(data: dict):
    try:
        address = data.get("address")
        label = data.get("label")
        txid = data.get("txid")
        amount = data.get("amount")
        ts = data.get("timestamp") or datetime.utcnow().isoformat()

        db = read_db()

        # Insert transaction
        db["transactions"].append({
            "txid": txid,
            "address": address,
            "amount": amount,
            "timestamp": ts
        })

        # Update wallet last_balance or add wallet if not exists
        found = False
        for w in db["wallets"]:
            if w["address"] == address:
                w["last_balance"] = amount
                found = True
                break
        if not found:
            db["wallets"].append({
                "user_id": "unknown",
                "label": label or "unknown",
                "address": address,
                "last_balance": amount
            })

        write_db(db)
        return JSONResponse({"status": "ok"})
    except Exception as e:
        return JSONResponse({"status": "error", "error": str(e)})

# Dashboard
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    db = read_db()
    wallets = [[w["user_id"], w["label"], w["address"], w.get("last_balance","0")] for w in db["wallets"]]
    txs = [[t["txid"], t["address"], t["amount"], t["timestamp"]] for t in db["transactions"][-20:][::-1]]
    return templates.TemplateResponse("index.html", {"request": request, "wallets": wallets, "txs": txs})

# Add wallet endpoint (optional)
@app.post("/add_wallet")
async def add_wallet(user_id: str = Form(...), label: str = Form(...), address: str = Form(...)):
    try:
        db = read_db()
        db["wallets"].append({
            "user_id": user_id,
            "label": label,
            "address": address,
            "last_balance": "0"
        })
        write_db(db)
        return JSONResponse({"status": "ok"})
    except Exception as e:
        return JSONResponse({"status": "error", "error": str(e)})

# Local run
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
