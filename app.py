# app.py
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timedelta
import httpx
import requests  # New: For CoinGecko price

app = FastAPI()

# Serve CSS
app.mount("/static", StaticFiles(directory="."), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Supabase
SUPABASE_URL = "https://enciwuvvqhnkkfourhkm.supabase.co"
SUPABASE_KEY = "sb_publishable_6cA5-fNu24sHcHxENX474Q__oCrovZR"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

# Get LTC price from CoinGecko
def get_ltc_price():
    try:
        resp = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd")
        return resp.json()["litecoin"]["usd"]
    except:
        return 0.0

# Ping endpoint
@app.get("/ping")
async def ping():
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": "99.9%",  # Placeholder; calculate from Supabase if needed
        "response_time": "50ms"
    }

# Get wallet balance via SoChain API
@app.get("/api/balance/{address}")
async def get_balance(address: str):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://chain.so/api/v2/get_address_balance/LTC/{address}")
            data = resp.json()
            balance = data.get("data", {}).get("confirmed_balance", "0")
            return {"balance": balance, "price_usd": get_ltc_price()}
    except Exception as e:
        return {"error": str(e)}

# Update stats on tx receive
@app.post("/api/tx")
async def receive_tx(data: dict):
    address = data.get("address")
    if not address:
        return JSONResponse({"status": "error", "error": "address required"}, status_code=400)

    payload = {
        "txid": data.get("txid") or "demo-tx",
        "address": address,
        "amount": str(data.get("amount") or "0"),
        "timestamp": data.get("timestamp") or datetime.utcnow().isoformat()
    }

    async with httpx.AsyncClient(timeout=5.0) as client:
        await client.post(f"{SUPABASE_URL}/rest/v1/transactions", headers=HEADERS, json=payload)
        await client.post(
            f"{SUPABASE_URL}/rest/v1/wallets",
            headers={**HEADERS, "Prefer": "resolution=merge-duplicates"},
            json={
                "user_id": "demo",
                "label": data.get("label", "demo"),
                "address": address,
                "last_balance": payload["amount"]
            }
        )
        # Update stats (increment users)
        await client.patch(
            f"{SUPABASE_URL}/rest/v1/stats?order=id.desc&limit=1",
            headers=HEADERS,
            json={"total_users": str(int((await client.get(f"{SUPABASE_URL}/rest/v1/wallets", headers=HEADERS)).json().__len__())), "last_update": datetime.utcnow().isoformat()}
        )
    return JSONResponse({"status": "ok"})

# Dashboard with stats
@app.get("/")
async def dashboard(request: Request):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            wallets = (await client.get(f"{SUPABASE_URL}/rest/v1/wallets", headers=HEADERS)).json()
            txs = (await client.get(f"{SUPABASE_URL}/rest/v1/transactions?order=id.desc&limit=20", headers=HEADERS)).json()
            stats = (await client.get(f"{SUPABASE_URL}/rest/v1/stats?order=id.desc&limit=1", headers=HEADERS)).json()
    except Exception as e:
        print("Supabase error:", e)
        wallets, txs, stats = [], [], [{"total_users": "0", "uptime": "0"}]

    ltc_price = get_ltc_price()
    total_ltc = sum(float(w.get("last_balance", 0)) for w in wallets)
    total_usd = total_ltc * ltc_price

    return templates.TemplateResponse("index.html", {
        "request": request, "wallets": wallets, "txs": txs, "stats": stats[0] if stats else {},
        "ltc_price": ltc_price, "total_ltc": total_ltc, "total_usd": total_usd
    })

# Add wallet (unchanged)
@app.post("/add_wallet")
async def add_wallet(user_id: str = Form(...), label: str = Form(...), address: str = Form(...)):
    async with httpx.AsyncClient() as client:
        await client.post(f"{SUPABASE_URL}/rest/v1/wallets", headers=HEADERS, json={
            "user_id": user_id, "label": label, "address": address, "last_balance": "0"
        })
    return JSONResponse({"status": "ok"})
