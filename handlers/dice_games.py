import asyncio
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from keyboards.inline import dice_menu_1, dice_menu_2, dice_menu_3
from math_engine import calc_1_dice, calc_2_dice, calc_3_dice
from utils.emoji import DOLLAR, WALLET, DICE, BET
from utils.notify import notify_result

router = Router()


def _parse_uid(call):
    parts = call.data.split(":")
    if parts and parts[-1].isdigit() and len(parts[-1]) > 5:
        return int(parts[-1])
    return call.from_user.id


def _check_owner(call, uid):
    return call.from_user.id == uid


async def _not_owner(call):
    await call.answer("❌ Это не твоя игра! Напиши свою команду.", show_alert=True)


@router.callback_query(F.data == "dice:1")
async def tab_1(call: types.CallbackQuery):
    await call.message.edit_text(f"{DICE} <b>Выберите исход игры!</b>",
                                 reply_markup=dice_menu_1(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "dice:2")
async def tab_2(call: types.CallbackQuery):
    await call.message.edit_text(f"{DICE} <b>Выберите исход игры!</b>",
                                 reply_markup=dice_menu_2(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "dice:3")
async def tab_3(call: types.CallbackQuery):
    await call.message.edit_text(f"{DICE} <b>Выберите исход игры!</b>",
                                 reply_markup=dice_menu_3(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "d1:allin")
async def d1_allin(call: types.CallbackQuery):
    uid = call.from_user.id
    bal = db.get_balance(uid)
    if bal <= 0:
        return await call.answer("❌ Нет баланса!", show_alert=True)
    db.set_bet(uid, bal)
    await call.message.edit_text(
        f"💥 <b>ВБ установлен: {bal:.2f}</b> {DOLLAR}\n\n"
        f"{DICE} Выберите исход игры:",
        reply_markup=dice_menu_1(), parse_mode="HTML")
    await call.answer("ВБ!")


@router.callback_query(F.data.startswith("d1:"))
async def play_1(call: types.CallbackQuery):
    if call.data == "d1:allin":
        return
    parts = call.data.split(":")
    choice = parts[1]
    uid = _parse_uid(call)
    if not _check_owner(call, uid):
        return await _not_owner(call)
    await _play(call, uid, 1, choice)


@router.callback_query(F.data.startswith("d2:"))
async def play_2(call: types.CallbackQuery):
    parts = call.data.split(":")
    choice = parts[1]
    uid = _parse_uid(call)
    if not _check_owner(call, uid):
        return await _not_owner(call)
    await _play(call, uid, 2, choice)


@router.callback_query(F.data.startswith("d3:"))
async def play_3(call: types.CallbackQuery):
    parts = call.data.split(":")
    choice = parts[1]
    uid = _parse_uid(call)
    if not _check_owner(call, uid):
        return await _not_owner(call)
    await _play(call, uid, 3, choice)


@router.callback_query(F.data.startswith("d1two:"))
async def play_1_two(call: types.CallbackQuery):
    parts = call.data.split(":")
    nums_str = parts[1]
    uid = _parse_uid(call)
    if not _check_owner(call, uid):
        return await _not_owner(call)
    nums = [int(x) for x in nums_str.split(",")]

    bet = db.get_bet(uid)
    if not db.has_enough(uid, bet):
        return await call.answer("❌ Недостаточно средств", show_alert=True)

    db.update_balance(uid, -bet)
    db.add_wager(uid, bet)
    db.inc_games(uid)

    await call.message.edit_text(
        f"{DICE} Бросаю... Ставка: <b>{bet}</b> {DOLLAR}", parse_mode="HTML")
    await call.answer()

    m = await call.message.answer_dice(emoji="🎲")
    await asyncio.sleep(3.5)
    v = m.dice.value

    if v in nums:
        win = round(bet * 2.8, 2)
        result = "win"
    else:
        win = 0
        result = "lose"

    await _finish(call, uid, "dice_1_two", v, bet, win, result,
                  2.8 if result == "win" else 0)


async def _play(call, uid, dtype, choice):
    bet = db.get_bet(uid)
    if not db.has_enough(uid, bet):
        return await call.answer(
            f"❌ Нужно {bet} 💵. Баланс: {db.get_balance(uid):.2f}",
            show_alert=True)

    db.update_balance(uid, -bet)
    db.add_wager(uid, bet)
    db.inc_games(uid)

    await call.message.edit_text(
        f"{DICE} Бросаю... Ставка: <b>{bet}</b> {DOLLAR}", parse_mode="HTML")
    await call.answer()

    if dtype == 1:
        m = await call.message.answer_dice(emoji="🎲")
        await asyncio.sleep(3.5)
        v = m.dice.value
        win, result = calc_1_dice(bet, choice, v)
        value = v
    elif dtype == 2:
        m1 = await call.message.answer_dice(emoji="🎲")
        await asyncio.sleep(3.5)
        m2 = await call.message.answer_dice(emoji="🎲")
        await asyncio.sleep(3.5)
        v1, v2 = m1.dice.value, m2.dice.value
        win, result = calc_2_dice(bet, choice, v1, v2)
        value = f"{v1} + {v2} = {v1+v2}"
    else:
        m1 = await call.message.answer_dice(emoji="🎲")
        await asyncio.sleep(3.5)
        m2 = await call.message.answer_dice(emoji="🎲")
        await asyncio.sleep(3.5)
        m3 = await call.message.answer_dice(emoji="🎲")
        await asyncio.sleep(3.5)
        v1, v2, v3 = m1.dice.value, m2.dice.value, m3.dice.value
        win, result = calc_3_dice(bet, choice, v1, v2, v3)
        value = f"{v1} + {v2} + {v3} = {v1+v2+v3}"

    mult = win / bet if bet and win > 0 else 0
    await _finish(call, uid, f"dice_{dtype}", value, bet, win, result, mult)


async def _finish(call, uid, game_key, value, bet, win, result, mult):
    row = db.cursor.execute("SELECT username FROM users WHERE user_id=?",
                             (uid,)).fetchone()
    uname = (row[0] if row and row[0] else f"id{uid}")
    mention = f'<a href="tg://user?id={uid}">{uname}</a>'

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Повторить",
                              callback_data=f"dice:1", style="success")],
        [InlineKeyboardButton(text="🎮 Меню игр",
                              callback_data="games_main", style="primary")],
    ])

    if result == "win":
        db.update_balance(uid, win)
        db.add_win(uid, win)
        db.add_game(uid, game_key, bet, win, mult, "win")
        new_bal = db.get_balance(uid)

        await call.message.reply(
            f"🔼 {mention} выигрывает <b>{win - bet:.2f}</b> {DOLLAR}\n\n"
            f"<blockquote>🎲 Выпало: <b>{value}</b>\n"
            f"{BET} Ставка: <b>{bet:.2f}</b> {DOLLAR}\n"
            f"{WALLET} Баланс: <b>{new_bal:.2f}</b> {DOLLAR}</blockquote>",
            reply_markup=kb, parse_mode="HTML")

        try:
            await notify_result(call.bot, uid, uname, "Кубик", str(value),
                                bet, win, mult, new_bal, True)
        except Exception as e:
            print(f"notify_win: {e}")
    else:
        db.add_loss(uid, bet)
        db.add_game(uid, game_key, bet, 0, 0, "lose")
        new_bal = db.get_balance(uid)

        await call.message.reply(
            f"🔽 {mention} проигрывает <b>{bet:.2f}</b> {DOLLAR}\n\n"
            f"<blockquote>🎲 Выпало: <b>{value}</b>\n"
            f"{BET} Ставка: <b>{bet:.2f}</b> {DOLLAR}\n"
            f"{WALLET} Баланс: <b>{new_bal:.2f}</b> {DOLLAR}</blockquote>",
            reply_markup=kb, parse_mode="HTML")

        try:
            await notify_result(call.bot, uid, uname, "Кубик", str(value),
                                bet, 0, 0, new_bal, False)
        except Exception as e:
            print(f"notify_lose: {e}")