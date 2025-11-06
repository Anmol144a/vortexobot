# app.py
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import httpx
import os
import traceback

app = FastAPI()

# CORS (safe for Vercel)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Mount static files FIRST (for style.css and potential favicon)
app.mount("/static", StaticFiles(directory="."), name="static")

# Templates - ensure dir exists
if not os.path.exists("templates"):
    raise RuntimeError("templates/ directory missing! Create it with index.html inside.")

templates = Jinja2Templates(directory="templates")

# HARDCODED SUPABASE
SUPABASE_URL = "https://enciwuvvqhnkkfourhkm.supabase.co"
SUPABASE_KEY = "sb_publishable_6cA5-fNu24sHcHxENX474Q__oCrovZR"

if not SUPABASE_KEY or SUPABASE_KEY.startswith("sb_publishable_"):  # Quick validation
    print("WARNING: Supabase key looks like a placeholder - test it!")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

# Global exception handler (logs to Vercel for debugging)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_msg = f"Global crash: {str(exc)}\n{traceback.format_exc()}"
    print(error_msg)  # Appears in Vercel logs
    return JSONResponse({"detail": "Internal Server Error"}, status_code=500)

# Favicon handler (prevents crash on /favicon.ico)
@app.get("/favicon.ico")
async def favicon():
    return FileResponse("favicon.ico", media_type="image/x-icon", background=None)  # Optional: Add a real favicon.ico or return 204

# Dashboard
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            wallets_resp = await client.get(f"{SUPABASE_URL}/rest/v1/wallets", headers=HEADERS)
            txs_resp = await client.get(f"{SUPABASE_URL}/rest/v1/transactions?order=id.desc&limit=20", headers=HEADERS)
            wallets_resp.raise_for_status()
            txs_resp.raise_for_status()
            wallets = wallets_resp.json()
            txs = txs_resp.json()
    except httpx.HTTPStatusError as e:
        print(f"Supabase HTTP error: {e.response.status_code} - {e.response.text[:200]}")
        wallets = []
        txs = []
    except Exception as e:
        print(f"Dashboard error: {str(e)}\n{traceback.format_exc()}")
        wallets = []
        txs = []

    return templates.TemplateResponse("index.html", {"request": request, "wallets": wallets, "txs": txs})

# Receive tx
@app.post("/api/tx")
async def receive_tx(data: dict):
    try:
        address = data.get("address")
        if not address:
            return JSONResponse({"status": "error", "error": "address required"}, status_code=400)

        payload_tx = {
            "txid": data.get("txid") or "demo-tx",
            "address": address,
            "amount": str(data.get("amount") or "0.0"),
            "timestamp": data.get("timestamp") or datetime.utcnow().isoformat()
        }
        label = data.get("label") or "demo"

        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(f"{SUPABASE_URL}/rest/v1/transactions", headers=HEADERS, json=payload_tx)

            wallet_payload = {
                "user_id": "demo",
                "label": label,
                "address": address,
                "last_balance": payload_tx["amount"]
            }
            await client.post(
                f"{SUPABASE_URL}/rest/v1/wallets",
                headers={**HEADERS, "Prefer": "resolution=merge-duplicates"},
                json=wallet_payload
            )
        return JSONResponse({"status": "ok"})
    except Exception as e:
        error_msg = f"Tx error: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return JSONResponse({"status": "error", "error": str(e)}, status_code=500)

# Add wallet
@app.post("/add_wallet")
async def add_wallet(user_id: str = Form(...), label: str = Form(...), address: str = Form(...)):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                f"{SUPABASE_URL}/rest/v1/wallets",
                headers=HEADERS,
                json={"user_id": user_id, "label": label, "address": address, "last_balance": "0"}
            )
        return JSONResponse({"status": "ok"})
    except Exception as e:
        print(f"Add wallet error: {str(e)}\n{traceback.format_exc()}")
        return JSONResponse({"status": "error", "error": str(e)}, status_code=500)
