import os
import aiohttp
import logging

log = logging.getLogger(__name__)

CRYPTO_TOKEN  = os.getenv("CRYPTO_BOT_TOKEN")
XROCKET_TOKEN = os.getenv("XROCKET_TOKEN")
CRYPTO_API  = "https://pay.crypt.bot/api"
XROCKET_API = "https://pay.api.xrocket.exchange/api/v1"


async def get_crypto_balance() -> float:
    """Возвращает баланс приложения в CryptoBot (USDT)."""
    if not CRYPTO_TOKEN:
        return 0.0
    headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{CRYPTO_API}/getBalance", headers=headers) as r:
                data = await r.json()
        if not data.get("ok"):
            log.error(f"[treasury] CryptoBot: {data}")
            return 0.0
        # Ответ вида {"result": [{"currency_code": "USDT", "available": "10.5"}]}
        for item in data["result"]:
            if item.get("currency_code") == "USDT":
                return float(item.get("available", 0))
        return 0.0
    except Exception as e:
        log.error(f"[treasury] CryptoBot ошибка: {e}")
        return 0.0


async def get_xrocket_balance() -> float:
    """Возвращает баланс приложения в xRocket (USDT)."""
    if not XROCKET_TOKEN:
        return 0.0
    headers = {
        "Authorization": f"Bearer {XROCKET_TOKEN}",
        "Accept": "application/json",
    }
    # Разные возможные эндпоинты
    urls = [
        f"{XROCKET_API}/me",
        f"{XROCKET_API}/balance",
        f"{XROCKET_API}/app/balance",
    ]
    for url in urls:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(url, headers=headers) as r:
                    if r.status != 200:
                        continue
                    data = await r.json()
            # Ищем баланс в ответе
            d = data.get("data") if isinstance(data, dict) else None
            if isinstance(d, dict):
                # USDT баланс
                bal = d.get("balance") or d.get("usdt") or 0
                if isinstance(bal, dict):
                    bal = bal.get("USDT", 0)
                return float(bal)
            if isinstance(data, dict) and "balance" in data:
                return float(data["balance"])
        except Exception:
            continue
    log.warning("[treasury] xRocket: не удалось получить баланс")
    return 0.0


async def get_treasury() -> dict:
    """Возвращает полную сводку по казне."""
    from database import db

    crypto_bal = await get_crypto_balance()
    xrocket_bal = await get_xrocket_balance()

    # Общие данные из БД
    db.cursor.execute("SELECT COALESCE(SUM(balance),0) FROM users")
    total_users_balance = db.cursor.fetchone()[0]

    db.cursor.execute("SELECT COALESCE(SUM(total_deposited),0) FROM users")
    total_deposited = db.cursor.fetchone()[0]

    db.cursor.execute("SELECT COALESCE(SUM(total_withdrawn),0) FROM users")
    total_withdrawn = db.cursor.fetchone()[0]

    db.cursor.execute("SELECT COALESCE(SUM(total_wagered),0) FROM users")
    total_wagered = db.cursor.fetchone()[0]

    db.cursor.execute("SELECT COALESCE(SUM(total_won),0) FROM users")
    total_won = db.cursor.fetchone()[0]

    # Профит казино = депозиты - выводы - баланс юзеров
    profit = total_deposited - total_withdrawn - total_users_balance

    return {
        "crypto": crypto_bal,
        "xrocket": xrocket_bal,
        "total_on_platforms": crypto_bal + xrocket_bal,
        "users_balance": total_users_balance,
        "deposited": total_deposited,
        "withdrawn": total_withdrawn,
        "wagered": total_wagered,
        "won": total_won,
        "profit": profit,
        "reserve": crypto_bal + xrocket_bal - total_users_balance,
    }