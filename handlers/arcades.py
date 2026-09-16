import asyncio
import random
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from math_engine import (
    mines_multiplier, tower_multiplier, generate_crash_point,
    roulette_multiplier
)
from utils.emoji import DOLLAR
from keyboards.inline import arcades_menu, mines_count_menu

router = Router()


# ============================================================
#                    АВТОРСКИЕ ИГРЫ
# ============================================================
@router.callback_query(F.data == "game:custom")
async def arcades_open(call: types.CallbackQuery):
    bet = db.get_bet(call.from_user.id)
    bal = db.get_balance(call.from_user.id)
    await call.message.edit_text(
        f"🎮 <b>Выберите игру для ставки!</b>\n\n"
        f"Ставка: <b>{bet}</b> {DOLLAR}\n"
        f"Баланс: <b>{bal:.2f}</b> {DOLLAR}",
        reply_markup=arcades_menu(), parse_mode="HTML"
    )
    await call.answer()


# ============================================================
#              MINES
# ============================================================
@router.callback_query(F.data == "ar:mines")
async def mines_menu_open(call: types.CallbackQuery):
    bet = db.get_bet(call.from_user.id)
    await call.message.edit_text(
        f"💣 <b>Мины</b>\n\n"
        f"Ставка: <b>{bet}</b> {DOLLAR}\n"
        f"Выберите количество мин (1-24):",
        reply_markup=mines_count_menu(), parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data.startswith("mines_n:"))
async def mines_start(call: types.CallbackQuery):
    mines = int(call.data.split(":")[1])
    uid = call.from_user.id
    bet = db.get_bet(uid)

    if not db.has_enough(uid, bet):
        return await call.answer(f"❌ Нужно {bet} 💵", show_alert=True)

    db.update_balance(uid, -bet)
    db.add_wager(uid, bet)
    db.inc_games(uid)

    mine_positions = set(random.sample(range(25), mines))
    data = f"{mines}|{','.join(map(str, sorted(mine_positions)))}|"
    db.set_active_game(uid, "mines", "playing", bet, 1.0, data)

    await _render_mines(call, uid, edit=True)
    await call.answer(f"💣 {mines} мин на поле")


def _parse_mines(data):
    parts = data.split("|")
    mines = int(parts[0]) if parts[0] else 5
    mine_pos = set(map(int, parts[1].split(","))) if len(parts) > 1 and parts[1] else set()
    opened = set(map(int, parts[2].split(","))) if len(parts) > 2 and parts[2] else set()
    return mines, mine_pos, opened


def _mines_kb(opened, mine_pos=None, reveal=False):
    rows = []
    for r in range(5):
        row = []
        for c in range(5):
            i = r * 5 + c
            if reveal and mine_pos and i in mine_pos:
                row.append(InlineKeyboardButton(text="💣", callback_data="mines_noop"))
            elif i in opened:
                row.append(InlineKeyboardButton(text="💎", callback_data="mines_noop"))
            elif reveal:
                row.append(InlineKeyboardButton(text="⬜", callback_data="mines_noop"))
            else:
                row.append(InlineKeyboardButton(text="⬜", callback_data=f"mines_open:{i}"))
        rows.append(row)
    return rows


async def _render_mines(call_or_msg, uid, edit=False):
    game = db.get_active_game(uid)
    if not game or game[0] != "mines":
        return

    _, _, bet, mult, data = game
    mines, mine_pos, opened = _parse_mines(data)

    rows = _mines_kb(opened)
    rows.append([InlineKeyboardButton(text=f"💰 Забрать {mult:.2f}x",
                                      callback_data="mines_cashout")])

    text = (
        f"💣 <b>Мины</b> ({mines} мин)\n"
        f"Открыто: <b>{len(opened)}</b> | Множитель: <b>{mult:.2f}x</b>\n"
        f"Ставка: <b>{bet}</b> {DOLLAR}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=rows)

    if edit and hasattr(call_or_msg, "message"):
        try:
            await call_or_msg.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
            return
        except Exception:
            pass
    await call_or_msg.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "mines_noop")
async def mines_noop(call: types.CallbackQuery):
    await call.answer()


@router.callback_query(F.data.startswith("mines_open:"))
async def mines_open(call: types.CallbackQuery):
    uid = call.from_user.id
    game = db.get_active_game(uid)
    if not game or game[0] != "mines":
        return await call.answer("❌ Игра не найдена", show_alert=True)

    _, _, bet, mult, data = game
    mines, mine_pos, opened = _parse_mines(data)

    idx = int(call.data.split(":")[1])
    if idx in opened:
        return await call.answer()

    # МИНА
    if idx in mine_pos:
        db.add_loss(uid, bet)
        db.add_game(uid, "mines", bet, 0, 0, "lose")
        db.delete_active_game(uid)
        rows = _mines_kb(opened, mine_pos, reveal=True)
        try:
            await call.message.edit_text(
                f"💥 <b>МИНА! Игра окончена</b>\n"
                f"Потеряно: <b>{bet}</b> {DOLLAR}\n"
                f"Баланс: <b>{db.get_balance(uid):.2f}</b>",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
                parse_mode="HTML"
            )
        except Exception:
            pass
        return await call.answer("💥 Мина!")

    # БЕЗОПАСНО
    opened.add(idx)
    new_mult = mines_multiplier(mines, len(opened))
    new_data = (f"{mines}|{','.join(map(str, sorted(mine_pos)))}|"
                f"{','.join(map(str, sorted(opened)))}")
    db.set_active_game(uid, "mines", "playing", bet, new_mult, new_data)

    await _render_mines(call, uid, edit=True)
    await call.answer(f"💎 {new_mult:.2f}x")


@router.callback_query(F.data == "mines_cashout")
async def mines_cashout(call: types.CallbackQuery):
    uid = call.from_user.id
    game = db.get_active_game(uid)
    if not game or game[0] != "mines":
        return await call.answer("❌ Игра не найдена", show_alert=True)

    _, _, bet, mult, data = game
    mines, mine_pos, opened = _parse_mines(data)

    if not opened:
        return await call.answer("❌ Откройте ячейку!", show_alert=True)

    win = round(bet * mult, 2)
    db.update_balance(uid, win)
    db.add_win(uid, win)
    db.add_game(uid, "mines", bet, win, mult, "win")
    db.delete_active_game(uid)

    await call.message.edit_text(
        f"💰 <b>Забрали!</b>\n"
        f"Множитель: <b>{mult:.2f}x</b>\n"
        f"Выигрыш: <b>+{win}</b> {DOLLAR}\n"
        f"Баланс: <b>{db.get_balance(uid):.2f}</b>",
        parse_mode="HTML"
    )
    await call.answer("✅ Выигрыш!")


# ============================================================
#              DICE (авторский, не Telegram)
# ============================================================
@router.callback_query(F.data == "ar:dice")
async def arcade_dice(call: types.CallbackQuery):
    uid = call.from_user.id
    bet = db.get_bet(uid)

    if not db.has_enough(uid, bet):
        return await call.answer(f"❌ Нужно {bet} 💵", show_alert=True)

    db.update_balance(uid, -bet)
    db.add_wager(uid, bet)
    db.inc_games(uid)

    player = random.randint(1, 6)
    dealer = random.randint(1, 6)
    win = round(bet * 2, 2) if player > dealer else 0.0

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Ещё", callback_data="ar:dice")],
        [InlineKeyboardButton(text="🏠 Главная", callback_data="back_to_main")],
    ])

    if win:
        db.update_balance(uid, win)
        db.add_win(uid, win)
        db.add_game(uid, "dice_arcade", bet, win, 2.0, "win")
        await call.message.edit_text(
            f"🎲 <b>Dice</b>\n\n"
            f"Вы: <b>{player}</b> | Дилер: <b>{dealer}</b>\n\n"
            f"✅ Выигрыш: <b>+{win}</b> {DOLLAR}\n"
            f"Баланс: <b>{db.get_balance(uid):.2f}</b>",
            reply_markup=kb, parse_mode="HTML"
        )
    else:
        db.add_loss(uid, bet)
        db.add_game(uid, "dice_arcade", bet, 0, 0, "lose")
        await call.message.edit_text(
            f"🎲 <b>Dice</b>\n\n"
            f"Вы: <b>{player}</b> | Дилер: <b>{dealer}</b>\n\n"
            f"❌ Проигрыш: <b>-{bet}</b> {DOLLAR}\n"
            f"Баланс: <b>{db.get_balance(uid):.2f}</b>",
            reply_markup=kb, parse_mode="HTML"
        )
    await call.answer()


# ============================================================
#              COINFLIP
# ============================================================
@router.callback_query(F.data == "ar:coinflip")
async def arcade_coinflip(call: types.CallbackQuery):
    uid = call.from_user.id
    bet = db.get_bet(uid)

    if not db.has_enough(uid, bet):
        return await call.answer(f"❌ Нужно {bet} 💵", show_alert=True)

    db.update_balance(uid, -bet)
    db.add_wager(uid, bet)
    db.inc_games(uid)

    result = random.choice(["Орёл", "Решка"])
    player_choice = random.choice(["Орёл", "Решка"])
    win = round(bet * 1.9, 2) if result == player_choice else 0.0

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Ещё", callback_data="ar:coinflip")],
        [InlineKeyboardButton(text="🏠 Главная", callback_data="back_to_main")],
    ])

    if win:
        db.update_balance(uid, win)
        db.add_win(uid, win)
        db.add_game(uid, "coinflip", bet, win, 1.9, "win")
        await call.message.edit_text(
            f"🪙 <b>Coinflip</b>\n\n"
            f"Выпало: <b>{result}</b>\n\n"
            f"✅ Выигрыш: <b>+{win}</b> {DOLLAR}\n"
            f"Баланс: <b>{db.get_balance(uid):.2f}</b>",
            reply_markup=kb, parse_mode="HTML"
        )
    else:
        db.add_loss(uid, bet)
        db.add_game(uid, "coinflip", bet, 0, 0, "lose")
        await call.message.edit_text(
            f"🪙 <b>Coinflip</b>\n\n"
            f"Выпало: <b>{result}</b>\n\n"
            f"❌ Проигрыш: <b>-{bet}</b> {DOLLAR}\n"
            f"Баланс: <b>{db.get_balance(uid):.2f}</b>",
            reply_markup=kb, parse_mode="HTML"
        )
    await call.answer()


# ============================================================
#              TOWER
# ============================================================
@router.callback_query(F.data == "ar:tower")
async def tower_start(call: types.CallbackQuery):
    uid = call.from_user.id
    bet = db.get_bet(uid)

    if not db.has_enough(uid, bet):
        return await call.answer(f"❌ Нужно {bet} 💵", show_alert=True)

    db.update_balance(uid, -bet)
    db.add_wager(uid, bet)
    db.inc_games(uid)
    db.set_active_game(uid, "tower", "playing", bet, 1.0, "0")
    await _render_tower(call, uid, edit=True)
    await call.answer()


def _tower_kb(mult, level):
    rows = [[InlineKeyboardButton(text="⬆️ Подняться", callback_data="tower_up")]]
    if level > 0:
        rows.append([InlineKeyboardButton(text=f"💰 Забрать {mult:.2f}x",
                                          callback_data="tower_cashout")])
    else:
        rows.append([InlineKeyboardButton(text="❌ Отмена",
                                          callback_data="tower_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _render_tower(call_or_msg, uid, edit=False):
    game = db.get_active_game(uid)
    if not game or game[0] != "tower":
        return
    _, _, bet, mult, data = game
    level = int(data)

    text = (
        f"🏰 <b>Башня</b>\n"
        f"Уровень: <b>{level}</b> | Множитель: <b>{mult:.2f}x</b>\n"
        f"Ставка: <b>{bet}</b> {DOLLAR}"
    )
    kb = _tower_kb(mult, level)

    if edit and hasattr(call_or_msg, "message"):
        try:
            await call_or_msg.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
            return
        except Exception:
            pass
    await call_or_msg.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "tower_up")
async def tower_up(call: types.CallbackQuery):
    uid = call.from_user.id
    game = db.get_active_game(uid)
    if not game or game[0] != "tower":
        return await call.answer("❌ Игра не найдена", show_alert=True)

    _, _, bet, mult, data = game
    level = int(data)

    if random.random() < 0.7:
        new_level = level + 1
        new_mult = tower_multiplier(new_level)
        db.set_active_game(uid, "tower", "playing", bet, new_mult, str(new_level))
        await _render_tower(call, uid, edit=True)
        await call.answer(f"✅ Уровень {new_level}!")
    else:
        db.add_loss(uid, bet)
        db.add_game(uid, "tower", bet, 0, 0, "lose")
        db.delete_active_game(uid)
        try:
            await call.message.edit_text(
                f"💥 <b>Сорвался на уровне {level}!</b>\n"
                f"Потеряно: <b>{bet}</b> {DOLLAR}\n"
                f"Баланс: <b>{db.get_balance(uid):.2f}</b>",
                parse_mode="HTML"
            )
        except Exception:
            pass
        await call.answer("💥")


@router.callback_query(F.data == "tower_cashout")
async def tower_cashout(call: types.CallbackQuery):
    uid = call.from_user.id
    game = db.get_active_game(uid)
    if not game or game[0] != "tower":
        return await call.answer("❌", show_alert=True)

    _, _, bet, mult, data = game
    level = int(data)
    if level <= 0:
        return await call.answer("❌ Сначала поднимись!", show_alert=True)

    win = round(bet * mult, 2)
    db.update_balance(uid, win)
    db.add_win(uid, win)
    db.add_game(uid, "tower", bet, win, mult, "win")
    db.delete_active_game(uid)

    await call.message.edit_text(
        f"💰 <b>Забрали!</b>\n"
        f"Уровень: <b>{level}</b> | <b>{mult:.2f}x</b>\n"
        f"Выигрыш: <b>+{win}</b> {DOLLAR}\n"
        f"Баланс: <b>{db.get_balance(uid):.2f}</b>",
        parse_mode="HTML"
    )
    await call.answer("✅")


@router.callback_query(F.data == "tower_cancel")
async def tower_cancel(call: types.CallbackQuery):
    uid = call.from_user.id
    game = db.get_active_game(uid)
    if game and game[0] == "tower":
        _, _, bet, mult, data = game
        db.update_balance(uid, bet)
        db.delete_active_game(uid)
    await call.message.edit_text("❌ Отменено, ставка возвращена.", parse_mode="HTML")
    await call.answer()


# ============================================================
#              РУЛЕТКА
# ============================================================
@router.callback_query(F.data == "ar:roulette")
async def roulette_start(call: types.CallbackQuery):
    uid = call.from_user.id
    bet = db.get_bet(uid)

    if not db.has_enough(uid, bet):
        return await call.answer(f"❌ Нужно {bet} 💵", show_alert=True)

    db.update_balance(uid, -bet)
    db.add_wager(uid, bet)
    db.inc_games(uid)

    number = random.randint(0, 36)
    reds = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
    color = "green" if number == 0 else ("red" if number in reds else "black")
    choice = "red"
    win, result = roulette_multiplier(bet, choice, number, color)
    color_emoji = {"red": "🔴", "black": "⚫", "green": "🟢"}[color]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Ещё раз", callback_data="ar:roulette")],
        [InlineKeyboardButton(text="🏠 Главная", callback_data="back_to_main")],
    ])

    if result == "win":
        db.update_balance(uid, win)
        db.add_win(uid, win)
        db.add_game(uid, "roulette", bet, win, 2.0, "win")
        await call.message.edit_text(
            f"🎡 <b>Рулетка</b>\n\n"
            f"Выпало: {color_emoji} <b>{number}</b>\n\n"
            f"✅ Выигрыш: <b>+{win}</b> {DOLLAR}\n"
            f"Баланс: <b>{db.get_balance(uid):.2f}</b>",
            reply_markup=kb, parse_mode="HTML"
        )
    else:
        db.add_loss(uid, bet)
        db.add_game(uid, "roulette", bet, 0, 0, "lose")
        await call.message.edit_text(
            f"🎡 <b>Рулетка</b>\n\n"
            f"Выпало: {color_emoji} <b>{number}</b>\n\n"
            f"❌ Проигрыш: <b>-{bet}</b> {DOLLAR}\n"
            f"Баланс: <b>{db.get_balance(uid):.2f}</b>",
            reply_markup=kb, parse_mode="HTML"
        )
    await call.answer()