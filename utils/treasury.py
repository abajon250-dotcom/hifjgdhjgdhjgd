import os
import aiohttp
import logging

log = logging.getLogger(__name__)

CRYPTO_TOKEN  = os.getenv("CRYPTO_BOT_TOKEN")
XROCKET_TOKEN = os.getenv("XROCKET_TOKEN")
CRYPTO_API    = "https://pay.crypt.bot/api"
XROCKET_API   = "https://pay.api.xrocket.exchange/api/v1"


async def get_crypto_balances() -> dict:
    """Все валюты CryptoBot: {'USDT': 17.49, 'TRX': 127.73, ...}"""
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
    """Пробуем разные эндпоинты xRocket, чтобы найти баланс."""
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

            # Вариант 1: {"balances": {"USDT": 23.43, "TON": 123}}
            if isinstance(d.get("balances"), dict):
                for k, v in d["balances"].items():
                    if isinstance(v, (int, float)) and v > 0:
                        out[k.upper()] = float(v)
                if out:
                    return out

            # Вариант 2: {"assets": [{"asset": "USDT", "balance": 23.43}]}
            if isinstance(d.get("assets"), list):
                for a in d["assets"]:
                    code = (a.get("asset") or a.get("currency") or "").upper()
                    bal = float(a.get("balance") or a.get("available") or 0)
                    if code and bal > 0:
                        out[code] = bal
                if out:
                    return out

            # Вариант 3: плоский dict
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

    # API-балансы USDT
    crypto_api_usdt = crypto.get("USDT", 0)
    xrocket_api_usdt = xrocket.get("USDT", 0)

    # Ручные добавки (то, что админ накрутил через кнопки)
    crypto_manual = manual.get("crypto", 0)
    xrocket_manual = manual.get("xrocket", 0)
    stars_manual = manual.get("stars", 0)
    hot_manual = manual.get("hot", 0)
    cold_manual = manual.get("cold", 0)

    # Итог по платёжкам
    crypto_total = crypto_api_usdt + crypto_manual
    xrocket_total = xrocket_api_usdt + xrocket_manual

    total_usdt = (crypto_total + xrocket_total +
                  stars_manual + hot_manual + cold_manual)

    return {
        "crypto": crypto,
        "xrocket": xrocket,
        "crypto_manual": crypto_manual,
        "xrocket_manual": xrocket_manual,
        "crypto_total": crypto_total,
        "xrocket_total": xrocket_total,
        "stars_manual": stars_manual,
        "hot_manual": hot_manual,
        "cold_manual": cold_manual,
        "users_balance": users_balance,
        "total_usdt": total_usdt,
        "reserve": total_usdt - users_balance,
    }