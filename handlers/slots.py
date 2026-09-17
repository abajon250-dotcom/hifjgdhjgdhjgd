import asyncio
import random
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from math_engine import spin_slots, calc_slots
from utils.emoji import DOLLAR, WALLET, BET, SLOTS
from utils.notify import notify_result, notify_bet
from utils.user_state import get_bet

router = Router()

SYMBOLS = ["7️⃣", "🍇", "🍋", "BAR"]


def _parse_uid(call: types.CallbackQuery) -> int:
    parts = call.data.split(":")
    if parts and parts[-1].isdigit() and len(parts[-1]) > 5:
        return int(parts[-1])
    return call.from_user.id


def _check_owner(call, uid) -> bool:
    return call.from_user.id == uid


async def _no(call):
    await call.answer("❌ Это не твоя игра!", show_alert=True)


@router.callback_query(F.data == "game:slots")
async def slots_open(call: types.CallbackQuery):
    from keyboards.inline import slots_menu
    bet = db.get_bet(call.from_user.id)
    await call.message.edit_text(
        f"{SLOTS} <b>Слоты</b>\n\n{BET} Ставка: <b>{bet}</b> {DOLLAR}",
        reply_markup=slots_menu(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("sl:"))
async def slots_play(call: types.CallbackQuery):
    parts = call.data.split(":")
    choice = parts[1]
    uid = _parse_uid(call)
    if not _check_owner(call, uid):
        return await _no(call)

    bet = db.get_bet(uid)
    if not db.has_enough(uid, bet):
        return await call.answer("❌ Недостаточно средств", show_alert=True)

    db.update_balance(uid, -bet)
    db.add_wager(uid, bet)
    db.inc_games(uid)

    try:
        row = db.cursor.execute("SELECT username FROM users WHERE user_id=?",
                                 (uid,)).fetchone()
        uname = row[0] if row and row[0] else f"id{uid}"
        await notify_bet(call.bot, uid, uname, "Слоты", bet, "🎰")
    except Exception:
        pass

    msg = await call.message.edit_text("🎰 | ❓ | ❓ | ❓ |")
    await call.answer()

    for _ in range(3):
        a, b, c = [random.choice(SYMBOLS) for _ in range(3)]
        try:
            await msg.edit_text(f"🎰 | {a} | {b} | {c} |")
        except Exception:
            pass
        await asyncio.sleep(0.4)

    reels = spin_slots()
    try:
        await msg.edit_text(f"🎰 | {reels[0]} | {reels[1]} | {reels[2]} |")
    except Exception:
        pass
    await asyncio.sleep(0.5)

    win, result = calc_slots(bet, choice, reels)
    reels_str = f"{reels[0]} {reels[1]} {reels[2]}"
    mult = win / bet if bet and win > 0 else 0

    row = db.cursor.execute("SELECT username FROM users WHERE user_id=?",
                             (uid,)).fetchone()
    uname = (row[0] if row and row[0] else f"id{uid}")
    mention = f'<a href="tg://user?id={uid}">{uname}</a>'

    repeat_cb = f"replay:slots:{choice}:{uid}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Повторить",
                              callback_data=repeat_cb, style="success")],
        [InlineKeyboardButton(text="🎮 Меню игр",
                              callback_data="games_main", style="primary")],
    ])

    if result == "win":
        db.update_balance(uid, win)
        db.add_win(uid, win)
        db.add_game(uid, "slots", bet, win, mult, "win")
        new_bal = db.get_balance(uid)

        from utils.refs import give_ref_bonus
        give_ref_bonus(uid, win)

        await call.message.reply(
            f"🔼 {mention} выигрывает <b>{win - bet:.2f}</b> {DOLLAR}\n\n"
            f"<blockquote>🎰 Выпало: {reels_str}\n"
            f"{BET} Ставка: <b>{bet:.2f}</b> {DOLLAR}\n"
            f"{WALLET} Баланс: <b>{new_bal:.2f}</b> {DOLLAR}</blockquote>",
            reply_markup=kb, parse_mode="HTML")

        try:
            await notify_result(call.bot, uid, uname, "Слоты", choice,
                                bet, win, mult, new_bal, True)
        except Exception:
            pass
    else:
        db.add_loss(uid, bet)
        db.add_game(uid, "slots", bet, 0, 0, "lose")
        new_bal = db.get_balance(uid)

        await call.message.reply(
            f"🔽 {mention} проигрывает <b>{bet:.2f}</b> {DOLLAR}\n\n"
            f"<blockquote>🎰 Выпало: {reels_str}\n"
            f"{BET} Ставка: <b>{bet:.2f}</b> {DOLLAR}\n"
            f"{WALLET} Баланс: <b>{new_bal:.2f}</b> {DOLLAR}</blockquote>",
            reply_markup=kb, parse_mode="HTML")

        try:
            await notify_result(call.bot, uid, uname, "Слоты", choice,
                                bet, 0, 0, new_bal, False)
        except Exception:
            pass


# ============================================================
#              ПРЯМОЙ ЗАПУСК СЛОТОВ (из текста и Повторить)
# ============================================================
async def play_slots_direct(message: types.Message, choice: str = "any",
                             uid: int = None):
    if uid is None:
        uid = message.from_user.id
    bet = get_bet(uid)
    if not db.has_enough(uid, bet):
        return await message.answer(
            f"❌ Нужно <b>{bet}</b> {DOLLAR}", parse_mode="HTML")

    db.update_balance(uid, -bet)
    db.add_wager(uid, bet)
    db.inc_games(uid)

    try:
        row = db.cursor.execute("SELECT username FROM users WHERE user_id=?",
                                 (uid,)).fetchone()
        uname = row[0] if row and row[0] else f"id{uid}"
        await notify_bet(message.bot, uid, uname, "Слоты", bet, "🎰")
    except Exception:
        pass

    msg = await message.answer("🎰 | ❓ | ❓ | ❓ |")
    for _ in range(3):
        a, b, c = [random.choice(SYMBOLS) for _ in range(3)]
        try:
            await msg.edit_text(f"🎰 | {a} | {b} | {c} |")
        except Exception:
            pass
        await asyncio.sleep(0.4)

    reels = spin_slots()
    try:
        await msg.edit_text(f"🎰 | {reels[0]} | {reels[1]} | {reels[2]} |")
    except Exception:
        pass
    await asyncio.sleep(0.5)

    win, result = calc_slots(bet, choice, reels)
    reels_str = f"{reels[0]} {reels[1]} {reels[2]}"
    mult = win / bet if bet and win > 0 else 0

    row = db.cursor.execute("SELECT username FROM users WHERE user_id=?",
                             (uid,)).fetchone()
    uname = (row[0] if row and row[0] else f"id{uid}")
    mention = f'<a href="tg://user?id={uid}">{uname}</a>'

    repeat_cb = f"replay:slots:{choice}:{uid}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Повторить",
                              callback_data=repeat_cb, style="success")],
        [InlineKeyboardButton(text="🎮 Меню игр",
                              callback_data="games_main", style="primary")],
    ])

    if result == "win":
        db.update_balance(uid, win)
        db.add_win(uid, win)
        db.add_game(uid, "slots", bet, win, mult, "win")
        new_bal = db.get_balance(uid)
        from utils.refs import give_ref_bonus
        give_ref_bonus(uid, win)

        await msg.edit_text(
            f"🔼 {mention} выигрывает <b>{win - bet:.2f}</b> {DOLLAR}\n\n"
            f"<blockquote>🎰 {reels_str}\n"
            f"{BET} Ставка: <b>{bet:.2f}</b> {DOLLAR}\n"
            f"{WALLET} Баланс: <b>{new_bal:.2f}</b> {DOLLAR}</blockquote>",
            reply_markup=kb, parse_mode="HTML")

        try:
            await notify_result(message.bot, uid, uname, "Слоты", choice,
                                bet, win, mult, new_bal, True)
        except Exception:
            pass
    else:
        db.add_loss(uid, bet)
        db.add_game(uid, "slots", bet, 0, 0, "lose")
        new_bal = db.get_balance(uid)

        await msg.edit_text(
            f"🔽 {mention} проигрывает <b>{bet:.2f}</b> {DOLLAR}\n\n"
            f"<blockquote>🎰 {reels_str}\n"
            f"{BET} Ставка: <b>{bet:.2f}</b> {DOLLAR}\n"
            f"{WALLET} Баланс: <b>{new_bal:.2f}</b> {DOLLAR}</blockquote>",
            reply_markup=kb, parse_mode="HTML")

        try:
            await notify_result(message.bot, uid, uname, "Слоты", choice,
                                bet, 0, 0, new_bal, False)
        except Exception:
            pass