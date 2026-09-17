import os
import aiohttp
import logging

log = logging.getLogger(__name__)

CRYPTO_TOKEN  = os.getenv("CRYPTO_BOT_TOKEN")
XROCKET_TOKEN = os.getenv("XROCKET_TOKEN")
CRYPTO_API    = "https://pay.crypt.bot/api"
XROCKET_API   = "https://pay.api.xrocket.exchange/api/v1"


async def get_crypto_balances() -> dict:
    if not CRYPTO_TOKEN:
        return {}
    headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{CRYPTO_API}/getBalance", headers=headers) as r:
                data = await r.json()
        if not data.get("ok"):
            return {}
        out = {}
        for item in data.get("result", []):
            code = item.get("currency_code", "")
            avail = float(item.get("available", 0))
            if avail > 0:
                out[code] = avail
        return out
    except Exception as e:
        log.error(f"[treasury] CryptoBot: {e}")
        return {}


async def get_xrocket_balances() -> dict:
    if not XROCKET_TOKEN:
        return {}
    headers = {
        "Authorization": f"Bearer {XROCKET_TOKEN}",
        "Accept": "application/json",
    }
    urls = [
        f"{XROCKET_API}/me",
        f"{XROCKET_API}/balance",
        f"{XROCKET_API}/app/balance",
        f"{XROCKET_API}/app/balances",
    ]
    for url in urls:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(url, headers=headers) as r:
                    if r.status != 200:
                        continue
                    data = await r.json()
            d = data.get("data", data) if isinstance(data, dict) else {}
            out = {}

            if isinstance(d.get("balances"), dict):
                for k, v in d["balances"].items():
                    if isinstance(v, (int, float)) and v > 0:
                        out[k.upper()] = float(v)
                if out:
                    return out

            if isinstance(d.get("assets"), list):
                for a in d["assets"]:
                    code = (a.get("asset") or a.get("currency") or "").upper()
                    bal = float(a.get("balance") or a.get("available") or 0)
                    if code and bal > 0:
                        out[code] = bal
                if out:
                    return out

            for k, v in d.items():
                if k.upper() in ("USDT", "TON", "TRX", "GRAM", "BTC", "ETH") and \
                   isinstance(v, (int, float)) and v > 0:
                    out[k.upper()] = float(v)
            if out:
                return out
        except Exception:
            continue
    return {}


async def get_full_treasury() -> dict:
    crypto = await get_crypto_balances()
    xrocket = await get_xrocket_balances()

    from database import db
    manual = db.get_treasury_manual()

    db.cursor.execute("SELECT COALESCE(SUM(balance),0) FROM users")
    users_balance = db.cursor.fetchone()[0]

    crypto_usdt = crypto.get("USDT", 0)
    xrocket_usdt = xrocket.get("USDT", 0)
    stars_manual = manual.get("stars", 0)
    hot_manual = manual.get("hot", 0)
    cold_manual = manual.get("cold", 0)

    total_usdt = crypto_usdt + xrocket_usdt + stars_manual + hot_manual + cold_manual

    return {
        "crypto": crypto,
        "xrocket": xrocket,
        "stars_manual": stars_manual,
        "hot_manual": hot_manual,
        "cold_manual": cold_manual,
        "users_balance": users_balance,
        "total_usdt": total_usdt,
        "reserve": total_usdt - users_balance,
    }