# app.py
import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
import httpx

app = FastAPI()
templates = Jinja2Templates(directory=".")  # index.html in root

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# Dashboard page
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    async with httpx.AsyncClient() as client:
        wallets_resp = await client.get(f"{SUPABASE_URL}/rest/v1/wallets", headers=HEADERS)
        txs_resp = await client.get(f"{SUPABASE_URL}/rest/v1/transactions?order=id.desc&limit=20", headers=HEADERS)
        wallets = wallets_resp.json()
        txs = txs_resp.json()
    return templates.TemplateResponse("index.html", {"request": request, "wallets": wallets, "txs": txs})

# Receive bot transactions
@app.post("/api/tx")
async def receive_tx(data: dict):
    try:
        payload_tx = {
            "txid": data.get("txid"),
            "address": data.get("address"),
            "amount": data.get("amount"),
            "timestamp": data.get("timestamp") or datetime.utcnow().isoformat()
        }
        address = data.get("address")
        label = data.get("label") or "unknown"

        async with httpx.AsyncClient() as client:
            # Insert transaction
            await client.post(f"{SUPABASE_URL}/rest/v1/transactions", headers=HEADERS, json=payload_tx)
            
            # Check wallet exists
            wallet_check = await client.get(f"{SUPABASE_URL}/rest/v1/wallets?address=eq.{address}", headers=HEADERS)
            wallet_data = wallet_check.json()
            
            if wallet_data:
                await client.patch(f"{SUPABASE_URL}/rest/v1/wallets?address=eq.{address}", headers=HEADERS,
                                   json={"last_balance": data.get("amount")})
            else:
                await client.post(f"{SUPABASE_URL}/rest/v1/wallets", headers=HEADERS,
                                  json={"user_id": "unknown", "label": label, "address": address, "last_balance": data.get("amount")})

        return JSONResponse({"status": "ok"})
    except Exception as e:
        return JSONResponse({"status": "error", "error": str(e)})

# Add wallet manually
@app.post("/add_wallet")
async def add_wallet(user_id: str = Form(...), label: str = Form(...), address: str = Form(...)):
    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{SUPABASE_URL}/rest/v1/wallets", headers=HEADERS,
                              json={"user_id": user_id, "label": label, "address": address, "last_balance": "0"})
        return JSONResponse({"status": "ok"})
    except Exception as e:
        return JSONResponse({"status": "error", "error": str(e)})
