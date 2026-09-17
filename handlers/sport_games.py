import asyncio
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from math_engine import (calc_football, calc_basketball,
                          calc_darts, calc_bowling, apply_win_commission)
from utils.emoji import DOLLAR, WALLET, BET
from utils.notify import notify_result, notify_bet, notify_dice
from utils.user_state import get_bet

router = Router()

GAME_LABEL = {"football": "футбол", "basketball": "баскет",
              "darts": "дартс", "bowling": "боулинг"}


def _parse_uid(call):
    parts = call.data.split(":")
    if parts and parts[-1].isdigit() and len(parts[-1]) > 5: return int(parts[-1])
    return call.from_user.id


def _check_owner(call, uid): return call.from_user.id == uid


async def _not_owner(call):
    await call.answer("❌ Это не твоя игра!", show_alert=True)


@router.callback_query(F.data.startswith("fc:"))
async def play_football(call: types.CallbackQuery):
    choice = call.data.split(":")[1]
    uid = _parse_uid(call)
    if not _check_owner(call, uid): return await _not_owner(call)
    await _play(call, uid, "football", "⚽", choice, calc_football)


@router.callback_query(F.data.startswith("bc:"))
async def play_basket(call: types.CallbackQuery):
    choice = call.data.split(":")[1]
    uid = _parse_uid(call)
    if not _check_owner(call, uid): return await _not_owner(call)
    await _play(call, uid, "basketball", "🏀", choice, calc_basketball)


@router.callback_query(F.data.startswith("dc:"))
async def play_darts(call: types.CallbackQuery):
    choice = call.data.split(":")[1]
    uid = _parse_uid(call)
    if not _check_owner(call, uid): return await _not_owner(call)
    await _play(call, uid, "darts", "🎯", choice, calc_darts)


@router.callback_query(F.data.startswith("wc:"))
async def play_bowling(call: types.CallbackQuery):
    choice = call.data.split(":")[1]
    uid = _parse_uid(call)
    if not _check_owner(call, uid): return await _not_owner(call)
    await _play(call, uid, "bowling", "🎳", choice, calc_bowling)


async def _bet_msg(target, uid, bet, label):
    row = db.cursor.execute("SELECT username FROM users WHERE user_id=?", (uid,)).fetchone()
    uname = row[0] if row and row[0] else f"id{uid}"
    mention = f'<a href="tg://user?id={uid}">{uname}</a>'
    await target.answer(f"🎲 {mention} поставил <b>{bet:.2f}$</b> на <b>{label}</b>",
                        parse_mode="HTML")


async def _play(call, uid, game, emoji, choice, calc_fn):
    bet = db.get_bet(uid)
    if not db.has_enough(uid, bet):
        return await call.answer("❌ Недостаточно средств", show_alert=True)
    db.update_balance(uid, -bet)
    db.add_wager(uid, bet)
    db.inc_games(uid)
    try:
        row = db.cursor.execute("SELECT username FROM users WHERE user_id=?", (uid,)).fetchone()
        uname = row[0] if row and row[0] else f"id{uid}"
        await notify_bet(call.bot, uid, uname, game.capitalize(), bet, emoji)
    except Exception: pass
    await _bet_msg(call.message, uid, bet, GAME_LABEL[game])
    await call.answer()
    m = await call.message.answer_dice(emoji=emoji)
    await asyncio.sleep(3.5)
    v = m.dice.value
    try: await notify_dice(call.bot, uid, m)
    except Exception: pass
    win, result = calc_fn(bet, choice, v)
    mult = win / bet if bet and win > 0 else 0
    row = db.cursor.execute("SELECT username FROM users WHERE user_id=?", (uid,)).fetchone()
    uname = row[0] if row and row[0] else f"id{uid}"
    mention = f'<a href="tg://user?id={uid}">{uname}</a>'
    repeat_cb = f"replay:sport_{game}:{choice}:{uid}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Повторить", callback_data=repeat_cb, style="success")],
        [InlineKeyboardButton(text="🎮 Меню игр", callback_data="games_main", style="primary")]])
    if result == "win":
        credited, comm = apply_win_commission(win)
        db.update_balance(uid, credited)
        db.add_win(uid, credited)
        db.add_game(uid, f"sport_{game}", bet, credited, mult, "win")
        new_bal = db.get_balance(uid)
        from utils.refs import give_ref_bonus
        give_ref_bonus(uid, credited)
        await call.message.reply(
            f"🔼 {mention} выигрывает <b>{credited - bet:.2f}</b> {DOLLAR}\n\n"
            f"<blockquote>{emoji} Выпало: <b>{v}</b>\n"
            f"{BET} Ставка: <b>{bet:.2f}</b> {DOLLAR}\n"
            f"{WALLET} Баланс: <b>{new_bal:.2f}</b> {DOLLAR}</blockquote>",
            reply_markup=kb, parse_mode="HTML")
        try:
            await notify_result(call.bot, uid, uname, game.capitalize(),
                                choice, bet, credited, mult, new_bal, True)
        except Exception: pass
    else:
        db.add_loss(uid, bet)
        db.add_game(uid, f"sport_{game}", bet, 0, 0, "lose")
        new_bal = db.get_balance(uid)
        await call.message.reply(
            f"🔽 {mention} проигрывает <b>{bet:.2f}</b> {DOLLAR}\n\n"
            f"<blockquote>{emoji} Выпало: <b>{v}</b>\n"
            f"{BET} Ставка: <b>{bet:.2f}</b> {DOLLAR}\n"
            f"{WALLET} Баланс: <b>{new_bal:.2f}</b> {DOLLAR}</blockquote>",
            reply_markup=kb, parse_mode="HTML")
        try:
            await notify_result(call.bot, uid, uname, game.capitalize(),
                                choice, bet, 0, 0, new_bal, False)
        except Exception: pass


async def play_sport_direct(message: types.Message, game: str, choice: str, uid: int = None):
    if uid is None: uid = message.from_user.id
    bet = get_bet(uid)
    if not db.has_enough(uid, bet):
        return await message.answer(
            f"❌ Нужно <b>{bet}</b> {DOLLAR}. Баланс: {db.get_balance(uid):.2f}",
            parse_mode="HTML")
    db.update_balance(uid, -bet)
    db.add_wager(uid, bet)
    db.inc_games(uid)
    emoji_map = {"football": "⚽", "basketball": "🏀", "darts": "🎯", "bowling": "🎳"}
    emoji = emoji_map[game]
    try:
        row = db.cursor.execute("SELECT username FROM users WHERE user_id=?", (uid,)).fetchone()
        uname = row[0] if row and row[0] else f"id{uid}"
        await notify_bet(message.bot, uid, uname, game.capitalize(), bet, emoji)
    except Exception: pass
    await _bet_msg(message, uid, bet, GAME_LABEL[game])
    m = await message.answer_dice(emoji=emoji)
    await asyncio.sleep(3.5)
    v = m.dice.value
    try: await notify_dice(message.bot, uid, m)
    except Exception: pass
    if game == "football": win, result = calc_football(bet, choice, v)
    elif game == "basketball": win, result = calc_basketball(bet, choice, v)
    elif game == "darts": win, result = calc_darts(bet, choice, v)
    else: win, result = calc_bowling(bet, choice, v)
    mult = win / bet if bet and win > 0 else 0
    row = db.cursor.execute("SELECT username FROM users WHERE user_id=?", (uid,)).fetchone()
    uname = row[0] if row and row[0] else f"id{uid}"
    mention = f'<a href="tg://user?id={uid}">{uname}</a>'
    repeat_cb = f"replay:sport_{game}:{choice}:{uid}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Повторить", callback_data=repeat_cb, style="success")],
        [InlineKeyboardButton(text="🎮 Меню игр", callback_data="games_main", style="primary")]])
    if result == "win":
        credited, comm = apply_win_commission(win)
        db.update_balance(uid, credited)
        db.add_win(uid, credited)
        db.add_game(uid, f"sport_{game}", bet, credited, mult, "win")
        new_bal = db.get_balance(uid)
        from utils.refs import give_ref_bonus
        give_ref_bonus(uid, credited)
        await message.answer(
            f"🔼 {mention} выигрывает <b>{credited - bet:.2f}</b> {DOLLAR}\n\n"
            f"<blockquote>{emoji} Выпало: <b>{v}</b>\n"
            f"{BET} Ставка: <b>{bet:.2f}</b> {DOLLAR}\n"
            f"{WALLET} Баланс: <b>{new_bal:.2f}</b> {DOLLAR}</blockquote>",
            reply_markup=kb, parse_mode="HTML")
        try:
            await notify_result(message.bot, uid, uname, game.capitalize(),
                                choice, bet, credited, mult, new_bal, True)
        except Exception: pass
    else:
        db.add_loss(uid, bet)
        db.add_game(uid, f"sport_{game}", bet, 0, 0, "lose")
        new_bal = db.get_balance(uid)
        await message.answer(
            f"🔽 {mention} проигрывает <b>{bet:.2f}</b> {DOLLAR}\n\n"
            f"<blockquote>{emoji} Выпало: <b>{v}</b>\n"
            f"{BET} Ставка: <b>{bet:.2f}</b> {DOLLAR}\n"
            f"{WALLET} Баланс: <b>{new_bal:.2f}</b> {DOLLAR}</blockquote>",
            reply_markup=kb, parse_mode="HTML")
        try:
            await notify_result(message.bot, uid, uname, game.capitalize(),
                                choice, bet, 0, 0, new_bal, False)
        except Exception: pass