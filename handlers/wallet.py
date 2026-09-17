import os
import aiohttp
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from keyboards.inline import withdraw_menu
from math_engine import apply_withdraw_commission
from utils.errors import format_error
from utils.emoji import CHECK_OK, WALLET2

router = Router()

CRYPTO_TOKEN  = os.getenv("CRYPTO_BOT_TOKEN")
XROCKET_TOKEN = os.getenv("XROCKET_TOKEN")
CRYPTO_API  = "https://pay.crypt.bot/api"
XROCKET_API = "https://pay.api.xrocket.exchange/api/v1"
MIN_WITHDRAW = 1.0


class WithdrawState(StatesGroup):
    waiting_amount = State()
    waiting_confirm = State()


@router.callback_query(F.data == "withdraw")
async def withdraw_handler(call: types.CallbackQuery):
    bal = db.get_balance(call.from_user.id)
    await call.message.edit_text(
        f"📥 <b>Вывод средств</b>\n\n"
        f"💵 Баланс: <b>{bal:.2f}</b>\n"
        f"Минимум: <b>{MIN_WITHDRAW} USDT</b>\n"
        f"⚠️ Комиссия: <b>0%</b>\n\n"
        f"Выберите метод:",
        reply_markup=withdraw_menu(), parse_mode="HTML")
    await call.answer()


@router.message(F.text.in_({"📥 Вывести", "Вывести", "вывести"}))
async def withdraw_msg(message: types.Message):
    bal = db.get_balance(message.from_user.id)
    await message.answer(
        f"📥 <b>Вывод средств</b>\n\n"
        f"💵 Баланс: <b>{bal:.2f}</b>\n"
        f"Минимум: <b>{MIN_WITHDRAW} USDT</b>\n"
        f"⚠️ Комиссия: <b>0%</b>",
        reply_markup=withdraw_menu(), parse_mode="HTML")


@router.callback_query(F.data.startswith("wd:"))
async def withdraw_method(call: types.CallbackQuery, state: FSMContext):
    method = call.data.split(":")[1]
    await state.update_data(method=method)

    data = await state.get_data()
    preset = data.get("wd_amount")
    if preset:
        amount = float(preset)
        bal = db.get_balance(call.from_user.id)
        if amount > bal:
            return await call.answer(f"❌ Недостаточно. Баланс: {bal:.2f}",
                                     show_alert=True)
        await state.update_data(amount=amount, wd_amount=None)
        payout, commission = apply_withdraw_commission(amount)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data="wd_confirm",
                                  style="success"),
             InlineKeyboardButton(text="❌ Отмена", callback_data="wd_cancel",
                                  style="danger")],
        ])
        await call.message.edit_text(
            f"Вывод: <b>{amount} USDT</b> через {method}\n"
            f"Комиссия: <b>{commission} USDT</b>\n"
            f"Получите: <b>{payout} USDT</b>\n\nПодтвердить?",
            reply_markup=kb, parse_mode="HTML")
        await state.set_state(WithdrawState.waiting_confirm)
        return await call.answer()

    bal = db.get_balance(call.from_user.id)
    await call.message.edit_text(
        f"💵 Баланс: <b>{bal:.2f}</b>\n\n"
        f"Введите сумму вывода (мин. {MIN_WITHDRAW}):",
        parse_mode="HTML")
    await state.set_state(WithdrawState.waiting_amount)
    await call.answer()


@router.message(WithdrawState.waiting_amount)
async def withdraw_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", ".").replace("$", "").strip())
        assert amount >= MIN_WITHDRAW
    except Exception:
        return await message.answer(
            f"❌ Минимум для вывода: <b>{MIN_WITHDRAW} USDT</b>",
            parse_mode="HTML")

    bal = db.get_balance(message.from_user.id)
    if amount > bal:
        return await message.answer(f"❌ Недостаточно. Баланс: {bal:.2f}")

    await state.update_data(amount=amount)
    data = await state.get_data()
    payout, commission = apply_withdraw_commission(amount)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="wd_confirm",
                              style="success"),
         InlineKeyboardButton(text="❌ Отмена", callback_data="wd_cancel",
                              style="danger")],
    ])
    await message.answer(
        f"Вывод: <b>{amount} USDT</b> через {data['method']}\n"
        f"Комиссия: <b>{commission} USDT</b>\n"
        f"Получите: <b>{payout} USDT</b>\n\nПодтвердить?",
        reply_markup=kb, parse_mode="HTML")
    await state.set_state(WithdrawState.waiting_confirm)


@router.callback_query(F.data == "wd_cancel", WithdrawState.waiting_confirm)
async def withdraw_cancel(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text("❌ Вывод отменён.")
    await state.clear()
    await call.answer()


@router.callback_query(F.data == "wd_confirm", WithdrawState.waiting_confirm)
async def withdraw_confirm(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    amount = data["amount"]
    method = data["method"]
    uid = call.from_user.id

    if db.get_balance(uid) < amount:
        await call.message.edit_text("❌ Недостаточно средств.")
        await state.clear()
        return await call.answer()

    payout, commission = apply_withdraw_commission(amount)
    await call.message.edit_text("⏳ Создаю заявку...")

    if method == "crypto":
        headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}
        payload = {
            "user_id": uid,
            "asset": "USDT",
            "amount": str(payout),
            "spend_id": f"wd_{uid}_{int(payout*100)}",
        }
        try:
            async with aiohttp.ClientSession() as s:
                async with s.post(f"{CRYPTO_API}/transfer", json=payload,
                                  headers=headers) as r:
                    resp = await r.json()
        except Exception:
            await call.message.edit_text(
                "❌ <b>Платёжный сервис недоступен</b>\nПопробуйте позже.")
            await state.clear()
            return await call.answer()

        if resp.get("ok"):
            db.update_balance(uid, -amount)
            db.add_withdraw(uid, amount)
            db.add_transaction(uid, "withdraw", "crypto",
                               amount, commission, "success")
            await call.message.edit_text(
                f"{CHECK_OK} <b>Вывод выполнен!</b>\n\n"
                f"💵 Отправлено: <b>{payout} USDT</b>\n"
                f"{WALLET2} Баланс: <b>{db.get_balance(uid):.2f}</b>",
                parse_mode="HTML")
        else:
            err = resp.get("error", {}) or {}
            if err.get("name") == "NOT_ENOUGH_COINS":
                msg = ("⚠️ <b>У казино нет средств на вывод</b>\n"
                       "Попробуйте xRocket.")
            elif err.get("name") == "AMOUNT_TOO_SMALL":
                msg = ("❌ <b>Слишком маленькая сумма</b>\n"
                       "CryptoBot принимает минимум <b>1 USDT</b>.")
            elif err.get("name") == "USER_NOT_FOUND":
                msg = ("❌ <b>Юзер не найден в CryptoBot</b>\n"
                       "Зайдите в @CryptoBot, привяжите аккаунт.")
            else:
                msg = f"❌ Ошибка CryptoBot: {resp}"
            await call.message.edit_text(msg, parse_mode="HTML")

    elif method == "xrocket":
        headers = {"Authorization": f"Bearer {XROCKET_TOKEN}",
                   "Content-Type": "application/json",
                   "Accept": "application/json"}
        payload = {
            "target": str(uid),
            "targetType": "telegram_user_id",
            "asset": "USDT",
            "amount": f"{float(payout):.2f}",
        }
        try:
            async with aiohttp.ClientSession() as s:
                async with s.post(f"{XROCKET_API}/payouts", json=payload,
                                  headers=headers) as r:
                    status_code = r.status
                    resp = await r.json()
        except Exception:
            await call.message.edit_text(
                "❌ <b>Платёжный сервис недоступен</b>\nПопробуйте позже.")
            await state.clear()
            return await call.answer()

        if status_code in (200, 201) and (resp.get("data") or resp.get("id")):
            db.update_balance(uid, -amount)
            db.add_withdraw(uid, amount)
            db.add_transaction(uid, "withdraw", "xrocket",
                               amount, commission, "success")
            await call.message.edit_text(
                f"{CHECK_OK} <b>Заявка на вывод создана!</b>\n\n"
                f"💵 Отправлено: <b>{payout} USDT</b>\n"
                f"{WALLET2} Баланс: <b>{db.get_balance(uid):.2f}</b>",
                parse_mode="HTML")
        else:
            await call.message.edit_text(format_error("xrocket", resp),
                                         parse_mode="HTML")

    await state.clear()
    await call.answer()