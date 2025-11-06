# app.py - Vortex LTC Tracker Backend (Full, Updated, Bech32 + Bot Status + Website Sync)

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
import os
from datetime import datetime, timezone

app = FastAPI()

# === CONFIG ===
VORTEX_URL = "https://vortex-panel-eight.vercel.app"
SUPABASE_URL = "https://enciwuvvqhnkkfourhkm.supabase.co"
SUPABASE_KEY = "sb_publishable_6cA5-fNu24sHcHxENX474Q__oCrovZR"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# === TEMPLATES & STATIC ===
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# === INDEX PAGE ===
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# === BOT STATUS ===
@app.get("/api/bot_status")
async def get_bot_status():
    try:
        async with httpx.AsyncClient() as client:
            status_res = await client.get(f"{SUPABASE_URL}/rest/v1/bot_status?order=id.desc&limit=1", headers=HEADERS)
            wallets_res = await client.get(f"{SUPABASE_URL}/rest/v1/wallets", headers=HEADERS)
            status = status_res.json()
            wallet_count = len(wallets_res.json())
            if status:
                status[0]["wallet_count"] = wallet_count
            return status
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# === WALLETS (with live balance) ===
@app.get("/api/wallets")
async def get_wallets():
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{SUPABASE_URL}/rest/v1/wallets", headers=HEADERS)
            wallets = res.json()
            enriched = []
            for w in wallets:
                try:
                    bal_res = await client.get(f"https://chain.so/api/v3/address/LTC/{w['address']}")
                    balance = bal_res.json().get("data", {}).get("balance", 0)
                except:
                    balance = 0
                enriched.append({
                    "id": w.get("id"),
                    "address": w["address"],
                    "label": w.get("label", "Unnamed"),
                    "alert_min": w.get("alert_min", 0.01),
                    "username": w.get("username", "Anon"),
                    "balance": float(balance)
                })
            return enriched
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# === TRANSACTIONS ===
@app.get("/api/transactions")
async def get_transactions():
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{SUPABASE_URL}/rest/v1/transactions?order=timestamp.desc&limit=10", headers=HEADERS)
            return res.json()
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# === ADD WALLET (Public Form) ===
@app.post("/api/add_wallet")
async def add_wallet(data: dict):
    addr = data.get("address", "").strip()
    if not (addr.startswith('L') or addr.startswith('ltc1')):
        return {"status": "error", "message": "Invalid address. Must start with L or ltc1"}
    
    payload = {
        "address": addr,
        "label": data.get("label", "Unnamed"),
        "alert_min": float(data.get("min", 0.01)),
        "username": "Website User"  # Public form
    }
    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{SUPABASE_URL}/rest/v1/wallets", headers=HEADERS, json=payload)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# === PUSH TX (from bot) ===
@app.post("/api/push-tx")
async def push_tx(data: dict):
    try:
        payload = {
            "txid": data.get("txid"),
            "address": data.get("address"),
            "amount": data.get("amount"),
            "from_addr": data.get("from_addr"),
            "timestamp": data.get("timestamp")
        }
        async with httpx.AsyncClient() as client:
            await client.post(f"{SUPABASE_URL}/rest/v1/transactions", headers=HEADERS, json=payload)
        return {"status": "ok"}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# === HEALTH CHECK ===
@app.get("/health")
async def health():
    return {"status": "healthy", "time": datetime.now(timezone.utc).isoformat()}

# === 404 ===
@app.get("/favicon.ico")
async def favicon():
    return JSONResponse({})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
