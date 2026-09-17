import os
import time
import aiohttp
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (LabeledPrice, PreCheckoutQuery,
                           InlineKeyboardMarkup, InlineKeyboardButton)
from database import db
from keyboards.inline import deposit_menu, deposit_amounts, games_main
from math_engine import apply_deposit_commission, MIN_DEPOSIT
from utils.emoji import (DOLLAR, WALLET, DEPOSIT, BET, GAMES, FLY_MONEY,
                          CRYPTOBOT, XROCKET, STARS)
from utils.errors import format_error
from utils.notify import notify_deposit

router = Router()

CRYPTO_TOKEN  = os.getenv("CRYPTO_BOT_TOKEN")
XROCKET_TOKEN = os.getenv("XROCKET_TOKEN")
CRYPTO_API  = "https://pay.crypt.bot/api"
XROCKET_API = "https://pay.xapi.xrocket.exchange/api/v1"


class DepositState(StatesGroup):
    waiting_custom_amount = State()
    waiting_stars_amount  = State()


def _after_deposit_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Играть", callback_data="games_main",
                              style="success")],
        [InlineKeyboardButton(text="💼 Кошелёк", callback_data="wallet",
                              style="primary")],
    ])


async def _show_after_deposit(message_or_call, uid, credited):
    db.get_user(uid)
    bal = db.get_balance(uid)
    bet = db.get_bet(uid)
    text = (f"✅ <b>Баланс пополнен на {credited:.2f} {DOLLAR}</b>\n\n"
            f"{GAMES} <b>Выбирайте игру!</b>\n\n"
            f"{DOLLAR} Баланс — <b>{bal:.2f}</b>\n"
            f"{BET} Ставка — <b>{bet}</b>")
    if hasattr(message_or_call, "answer"):
        await message_or_call.answer(text, reply_markup=_after_deposit_kb(),
                                     parse_mode="HTML")


async def _notify_deposit_safe(bot, uid, credited):
    try:
        row = db.cursor.execute("SELECT username FROM users WHERE user_id=?",
                                (uid,)).fetchone()
        uname = row[0] if row and row[0] else f"id{uid}"
        await notify_deposit(bot, uid, uname, credited)
    except Exception as e:
        print(f"notify_deposit error: {e}")


@router.callback_query(F.data == "deposit")
async def deposit_handler(call: types.CallbackQuery):
    uid = call.from_user.id
    db.get_user(uid)
    bal = db.get_balance(uid)
    bet = db.get_bet(uid)
    await call.message.edit_text(
        f"{DEPOSIT} <b>ПОПОЛНЕНИЕ БАЛАНСА</b>\n\n"
        f"{DOLLAR} Баланс: <b>{bal:.2f}</b>\n"
        f"{BET} Ставка: <b>{bet}</b>\n\n"
        f"⚠️ Комиссия: <b>5%</b> | Минимум: <b>{MIN_DEPOSIT} USDT</b>\n\n"
        f"<b>Выберите способ 👇</b>",
        reply_markup=deposit_menu(), parse_mode="HTML")
    await call.answer()


@router.message(F.text.in_({"📤 Пополнить", "Пополнить", "пополнить", "деп"}))
async def deposit_msg(message: types.Message):
    uid = message.from_user.id
    db.get_user(uid)
    bal = db.get_balance(uid)
    bet = db.get_bet(uid)
    await message.answer(
        f"{DEPOSIT} <b>ПОПОЛНЕНИЕ БАЛАНСА</b>\n\n"
        f"{DOLLAR} Баланс: <b>{bal:.2f}</b>\n"
        f"{BET} Ставка: <b>{bet}</b>\n\n"
        f"⚠️ Комиссия: <b>5%</b> | Минимум: <b>{MIN_DEPOSIT} USDT</b>\n\n"
        f"<b>Выберите способ 👇</b>",
        reply_markup=deposit_menu(), parse_mode="HTML")


@router.callback_query(F.data.startswith("dep:"))
async def deposit_method(call: types.CallbackQuery, state: FSMContext):
    method = call.data.split(":")[1]
    data = await state.get_data()
    preset_amount = data.get("dep_amount")
    if preset_amount:
        await state.update_data(dep_amount=None)
        return await _process_deposit(call, method, float(preset_amount))
    if method == "stars":
        await call.message.edit_text(
            f"⭐ <b>Пополнение через Telegram Stars</b>\n\n"
            f"Введите количество звёзд (минимум 50).\n"
            f"Курс: 1 ⭐ = 0.013 USDT", parse_mode="HTML")
        await state.set_state(DepositState.waiting_stars_amount)
        return await call.answer()
    await call.message.edit_text(
        f"Выберите сумму пополнения (мин. <b>{MIN_DEPOSIT} USDT</b>):",
        reply_markup=deposit_amounts(method), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("depamt:"))
async def create_deposit(call: types.CallbackQuery):
    _, method, amount = call.data.split(":")
    await _process_deposit(call, method, float(amount))


@router.callback_query(F.data.startswith("depcustom:"))
async def custom_deposit(call: types.CallbackQuery, state: FSMContext):
    method = call.data.split(":")[1]
    await state.update_data(dep_method=method)
    await call.message.edit_text(
        f"✏️ <b>Введите свою сумму</b> (мин. {MIN_DEPOSIT} USDT):",
        parse_mode="HTML")
    await state.set_state(DepositState.waiting_custom_amount)
    await call.answer()


@router.message(DepositState.waiting_custom_amount)
async def process_custom_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", ".").replace("$", "").strip())
        if amount < MIN_DEPOSIT:
            raise ValueError
    except Exception:
        return await message.answer(f"❌ Введите число ≥ {MIN_DEPOSIT}")
    data = await state.get_data()
    method = data["dep_method"]
    await state.clear()

    class F:
        def __init__(s, m):
            s.from_user = m.from_user
            s.message = m
        async def answer(s, *a, **k): pass

    await _process_deposit(F(message), method, amount)


async def _process_deposit(call, method: str, amount: float):
    uid = call.from_user.id
    credited, commission = apply_deposit_commission(amount)

    if method == "crypto":
        headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}
        payload = {"asset": "USDT", "amount": str(amount),
                   "description": "Пополнение баланса",
                   "payload": f"crypto:{uid}:{credited}",
                   "expires_in": 900}
        try:
            async with aiohttp.ClientSession() as s:
                async with s.post(f"{CRYPTO_API}/createInvoice", json=payload,
                                  headers=headers) as r:
                    data = await r.json()
        except Exception:
            return await call.message.answer("❌ Сервис недоступен.")
        if not data.get("ok"):
            return await call.message.answer(format_error("crypto", data),
                                             parse_mode="HTML")
        inv = data["result"]
        db.add_transaction(uid, "deposit", "crypto", amount, commission,
                           "pending", str(inv["invoice_id"]))
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Оплатить", url=inv["bot_invoice_url"],
                                  style="success")],
            [InlineKeyboardButton(text="Я оплатил",
                                  callback_data=f"chk:crypto:{inv['invoice_id']}",
                                  style="primary")]])
        await call.message.answer(
            f"{CRYPTOBOT} <b>Счёт CryptoBot на {amount} USDT</b>\n"
            f"⏱ Действует <b>15 минут</b>", reply_markup=kb, parse_mode="HTML")
        return

    if method == "xrocket":
        headers = {"Authorization": f"Bearer {XROCKET_TOKEN}",
                   "Content-Type": "application/json",
                   "Accept": "application/json"}
        payload = {"priceAmount": str(float(amount)), "priceCurrency": "USDT",
                   "payoutCurrency": "USDT", "payCurrencies": ["USDT"],
                   "description": "Пополнение баланса",
                   "clientInvoiceId": f"dep_{uid}_{int(amount*100)}_{int(time.time())}",
                   "expiresIn": 900000,
                   "customer": {"telegramId": str(uid)}}
        try:
            async with aiohttp.ClientSession() as s:
                async with s.post(f"{XROCKET_API}/invoices", json=payload,
                                  headers=headers) as r:
                    status_code = r.status
                    data = await r.json()
        except Exception:
            return await call.message.answer("❌ Сервис недоступен.")
        if status_code >= 400:
            return await call.message.answer(format_error("xrocket", data),
                                             parse_mode="HTML")
        inv_id = data.get("id")
        links = data.get("links", {}) or {}
        link = links.get("telegramBotLink") or links.get("webLink") or data.get("link")
        if not link:
            return await call.message.answer("❌ Не удалось создать счёт.")
        db.add_transaction(uid, "deposit", "xrocket", amount, commission,
                           "pending", str(inv_id or ""))
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Оплатить", url=link, style="success")],
            [InlineKeyboardButton(text="Я оплатил",
                                  callback_data=f"chk:xrocket:{inv_id or ''}",
                                  style="primary")]])
        await call.message.answer(
            f"{XROCKET} <b>Счёт xRocket на {amount} USDT</b>\n"
            f"⏱ Действует <b>15 минут</b>", reply_markup=kb, parse_mode="HTML")


@router.message(DepositState.waiting_stars_amount)
async def stars_amount(message: types.Message, state: FSMContext):
    try:
        stars = int(message.text.strip())
        if stars < 50: raise ValueError
    except Exception:
        return await message.answer("❌ Введите целое число ≥ 50")
    prices = [LabeledPrice(label="Пополнение", amount=stars)]
    await message.answer_invoice(title="Пополнение баланса",
                                 description=f"Покупка {stars} звёзд",
                                 payload=f"stars:{stars}",
                                 provider_token="", currency="XTR", prices=prices)
    await state.clear()


@router.callback_query(F.data.startswith("chk:"))
async def check_payment(call: types.CallbackQuery):
    parts = call.data.split(":")
    provider = parts[1]
    invoice_id = parts[2] if len(parts) > 2 else ""
    uid = call.from_user.id

    if provider == "crypto":
        headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(f"{CRYPTO_API}/getInvoices", headers=headers,
                                 params={"invoice_ids": invoice_id}) as r:
                    data = await r.json()
        except Exception:
            return await call.answer("❌ Сервис недоступен.", show_alert=True)
        items = data.get("result", {}).get("items", [])
        if items and items[0].get("status") == "paid":
            payload = items[0].get("payload", "")
            credited = float(payload.split(":")[2]) if ":" in payload else 0
            db.update_balance(uid, credited)
            db.add_deposit(uid, credited)
            db.add_transaction(uid, "deposit", "crypto", credited, 0.0,
                               "success", invoice_id)
            await _notify_deposit_safe(call.bot, uid, credited)
            await call.message.delete()
            await _show_after_deposit(call.message, uid, credited)
            return await call.answer()
        return await call.answer("❌ Оплата ещё не поступила.", show_alert=True)

    if provider == "xrocket":
        if not invoice_id:
            return await call.answer("❌ Счёт не найден.", show_alert=True)
        headers = {"Authorization": f"Bearer {XROCKET_TOKEN}",
                   "Accept": "application/json"}
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(f"{XROCKET_API}/invoices", headers=headers,
                                 params={"id": invoice_id}) as r:
                    status_code = r.status
                    data = await r.json()
        except Exception:
            return await call.answer("❌ Сервис недоступен.", show_alert=True)
        if status_code != 200:
            return await call.answer("❌ Не удалось проверить.", show_alert=True)
        items = data.get("items", []) if isinstance(data, dict) else []
        if not items:
            return await call.answer("❌ Счёт не найден.", show_alert=True)
        inv = items[0]
        status = inv.get("status", "")
        if status in ("paid", "success", "completed"):
            credited = float(inv.get("priceAmount", 0))
            db.update_balance(uid, credited)
            db.add_deposit(uid, credited)
            db.add_transaction(uid, "deposit", "xrocket", credited, 0.0,
                               "success", str(invoice_id))
            await _notify_deposit_safe(call.bot, uid, credited)
            await call.message.delete()
            await _show_after_deposit(call.message, uid, credited)
            return await call.answer()
        status_ru = {"active": "ожидает оплаты", "expired": "истёк"}.get(status, status)
        return await call.answer(f"⏳ Счёт: {status_ru}", show_alert=True)


@router.pre_checkout_query()
async def pre_checkout(q: PreCheckoutQuery):
    await q.answer(ok=True)


@router.message(F.successful_payment)
async def stars_paid(message: types.Message):
    payload = message.successful_payment.invoice_payload
    try:
        stars = int(payload.split(":")[1])
    except Exception:
        stars = int(message.successful_payment.total_amount)
    usd = round(stars * 0.013, 2)
    db.update_balance(message.from_user.id, usd)
    db.add_deposit(message.from_user.id, usd)
    db.add_transaction(message.from_user.id, "deposit", "stars", usd, 0.0, "success")
    await _notify_deposit_safe(message.bot, message.from_user.id, usd)
    await _show_after_deposit(message, message.from_user.id, usd)