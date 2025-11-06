# app.py
import requests
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory=".")

SUPABASE_URL = "https://enciwuvvqhnkkfourhkm.supabase.co"
SUPABASE_KEY = "sb_publishable_6cA5-fNu24sHcHxENX474Q__oCrovZR"
HEADERS = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    wallets = requests.get(f"{SUPABASE_URL}/rest/v1/wallets", headers=HEADERS).json()
    txs = requests.get(f"{SUPABASE_URL}/rest/v1/transactions?order=id.desc&limit=20", headers=HEADERS).json()
    return templates.TemplateResponse("index.html", {"request": request, "wallets": wallets, "txs": txs})

@app.post("/api/tx")
async def receive_tx(data: dict):
    try:
        payload = {
            "txid": data.get("txid"),
            "address": data.get("address"),
            "amount": data.get("amount"),
            "timestamp": data.get("timestamp") or datetime.utcnow().isoformat()
        }
        requests.post(f"{SUPABASE_URL}/rest/v1/transactions", headers=HEADERS, json=payload)
        address = data.get("address")
        label = data.get("label") or "unknown"
        r = requests.get(f"{SUPABASE_URL}/rest/v1/wallets?address=eq.{address}", headers=HEADERS).json()
        if r:
            requests.patch(f"{SUPABASE_URL}/rest/v1/wallets?address=eq.{address}", headers=HEADERS,
                           json={"last_balance": data.get("amount")})
        else:
            requests.post(f"{SUPABASE_URL}/rest/v1/wallets", headers=HEADERS,
                          json={"user_id": "unknown", "label": label, "address": address, "last_balance": data.get("amount")})
        return JSONResponse({"status": "ok"})
    except Exception as e:
        return JSONResponse({"status": "error", "error": str(e)})

@app.post("/add_wallet")
async def add_wallet(user_id: str = Form(...), label: str = Form(...), address: str = Form(...)):
    try:
        requests.post(f"{SUPABASE_URL}/rest/v1/wallets", headers=HEADERS,
                      json={"user_id": user_id, "label": label, "address": address, "last_balance": "0"})
        return JSONResponse({"status": "ok"})
    except Exception as e:
        return JSONResponse({"status": "error", "error": str(e)})
