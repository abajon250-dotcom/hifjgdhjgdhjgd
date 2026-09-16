import asyncio
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from keyboards.inline import dice_menu_1, dice_menu_2, dice_menu_3
from math_engine import calc_1_dice, calc_2_dice, calc_3_dice
from utils.emoji import DOLLAR, WALLET, DICE, WIN_LOSS, LOSE_LOSS, BET
from utils.notify import notify_result

router = Router()


# ============================================================
#                    ТАБЫ
# ============================================================
@router.callback_query(F.data == "dice:1")
async def tab_1(call: types.CallbackQuery):
    bal = db.get_balance(call.from_user.id)
    await call.message.edit_text(
        f"{DICE} <b>Выберите исход игры!</b>\n\n"
        f"{WALLET} Баланс: <b>{bal:.2f}</b> {DOLLAR}",
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


# ============================================================
#              ВБ — ВЕСЬ БАЛАНС
# ============================================================
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


# ============================================================
#                    ЗАПУСК ИГРЫ
# ============================================================
@router.callback_query(F.data.startswith("d1:"))
async def play_1(call: types.CallbackQuery):
    if call.data == "d1:allin":
        return
    await _play(call, 1, call.data.split(":", 1)[1])


@router.callback_query(F.data.startswith("d2:"))
async def play_2(call: types.CallbackQuery):
    await _play(call, 2, call.data.split(":", 1)[1])


@router.callback_query(F.data.startswith("d3:"))
async def play_3(call: types.CallbackQuery):
    await _play(call, 3, call.data.split(":", 1)[1])


async def _play(call: types.CallbackQuery, dtype: int, choice: str):
    uid = call.from_user.id
    bet = db.get_bet(uid)

    if not db.has_enough(uid, bet):
        return await call.answer(
            f"❌ Нужно {bet} 💵. Баланс: {db.get_balance(uid):.2f}",
            show_alert=True)

    db.update_balance(uid, -bet)
    db.add_wager(uid, bet)
    db.inc_games(uid)

    await call.message.edit_text(
        f"{DICE} Бросаю... Ставка: <b>{bet}</b> {DOLLAR}",
        parse_mode="HTML")
    await call.answer()

    # ---------- БРОСКИ ----------
    if dtype == 1:
        m = await call.message.answer_dice(emoji="🎲")
        await asyncio.sleep(3.5)
        v = m.dice.value
        win, result = calc_1_dice(bet, choice, v)
        dice_text = f"🎲 Выпало: <b>{v}</b>"
        game_name = "Один куб"
    elif dtype == 2:
        m1 = await call.message.answer_dice(emoji="🎲")
        await asyncio.sleep(3.5)
        m2 = await call.message.answer_dice(emoji="🎲")
        await asyncio.sleep(3.5)
        v1, v2 = m1.dice.value, m2.dice.value
        win, result = calc_2_dice(bet, choice, v1, v2)
        dice_text = (f"🎲 Выпало: <b>{v1}</b> и <b>{v2}</b>\n"
                     f"Сумма: <b>{v1 + v2}</b> | Произведение: <b>{v1 * v2}</b>")
        game_name = "Два куба"
    else:
        m1 = await call.message.answer_dice(emoji="🎲")
        await asyncio.sleep(3.5)
        m2 = await call.message.answer_dice(emoji="🎲")
        await asyncio.sleep(3.5)
        m3 = await call.message.answer_dice(emoji="🎲")
        await asyncio.sleep(3.5)
        v1, v2, v3 = m1.dice.value, m2.dice.value, m3.dice.value
        win, result = calc_3_dice(bet, choice, v1, v2, v3)
        dice_text = (f"🎲 Выпало: <b>{v1}</b>, <b>{v2}</b>, <b>{v3}</b>\n"
                     f"Сумма: <b>{v1 + v2 + v3}</b>")
        game_name = "Три куба"

    # ---------- USERNAME ----------
    row = db.cursor.execute("SELECT username FROM users WHERE user_id=?",
                             (uid,)).fetchone()
    uname = (row[0] if row and row[0] else f"id{uid}")
    mention = f'<a href="tg://user?id={uid}">{uname}</a>'

    # ---------- КЛАВИАТУРА ----------
    kb_bottom = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"-{bet:.2f}", callback_data=f"betdec:{dtype}",
                              style="danger"),
         InlineKeyboardButton(text="Повторить", callback_data=f"repeat:{dtype}:{choice}",
                              style="primary"),
         InlineKeyboardButton(text=f"+{bet:.2f}", callback_data=f"betinc:{dtype}",
                              style="success")],
        [InlineKeyboardButton(text="Пополнить", callback_data="deposit",
                              icon_custom_emoji_id="5445355530111437729",
                              style="success"),
         InlineKeyboardButton(text="Вывести", callback_data="withdraw",
                              icon_custom_emoji_id="5443127283898405358",
                              style="danger")],
    ])

    mult = round(win / bet, 2) if bet else 0

    # ---------- РЕЗУЛЬТАТ ----------
    if result == "win":
        db.update_balance(uid, win)
        db.add_win(uid, win)
        db.add_game(uid, f"dice_{dtype}", bet, win, mult, "win")
        new_balance = db.get_balance(uid)

        header = (
            f"{WIN_LOSS} {mention} выигрывает <b>{win - bet:.2f}</b> {DOLLAR}\n\n"
            f"<blockquote>{dice_text}\n"
            f"{BET} Ставка: <b>{bet:.2f}</b> {DOLLAR}\n"
            f"{WALLET} Баланс: <b>{new_balance:.2f}</b> {DOLLAR}</blockquote>"
        )
        await call.message.answer(header, reply_markup=kb_bottom, parse_mode="HTML")

        # Уведомление в канал
        try:
            await notify_result(
                call.bot, uid, call.from_user.username or "player",
                game_name, choice, bet, win, mult, new_balance, True
            )
        except Exception as e:
            print(f"notify_result: {e}")
    else:
        db.add_loss(uid, bet)
        db.add_game(uid, f"dice_{dtype}", bet, 0, 0, "lose")
        new_balance = db.get_balance(uid)

        header = (
            f"{LOSE_LOSS} {mention} проигрывает <b>{bet:.2f}</b> {DOLLAR}\n\n"
            f"<blockquote>{dice_text}\n"
            f"{BET} Ставка: <b>{bet:.2f}</b> {DOLLAR}\n"
            f"{WALLET} Баланс: <b>{new_balance:.2f}</b> {DOLLAR}</blockquote>"
        )
        await call.message.answer(header, reply_markup=kb_bottom, parse_mode="HTML")

        # Уведомление в канал (только если ставка крупная)
        try:
            await notify_result(
                call.bot, uid, call.from_user.username or "player",
                game_name, choice, bet, 0.0, mult, new_balance, False
            )
        except Exception as e:
            print(f"notify_result: {e}")


# ============================================================
#              БЫСТРЫЕ КНОПКИ + / - / ПОВТОР
# ============================================================
@router.callback_query(F.data.startswith("betdec:"))
async def bet_dec(call: types.CallbackQuery):
    uid = call.from_user.id
    cur = db.get_bet(uid)
    new = max(0.5, round(cur - max(0.5, cur * 0.2), 2))
    db.set_bet(uid, new)
    await call.answer(f"Ставка: {new}")


@router.callback_query(F.data.startswith("betinc:"))
async def bet_inc(call: types.CallbackQuery):
    uid = call.from_user.id
    cur = db.get_bet(uid)
    new = round(cur + max(0.5, cur * 0.2), 2)
    db.set_bet(uid, new)
    await call.answer(f"Ставка: {new}")


@router.callback_query(F.data.startswith("repeat:"))
async def repeat(call: types.CallbackQuery):
    _, dtype, choice = call.data.split(":", 2)
    await _play(call, int(dtype), choice)