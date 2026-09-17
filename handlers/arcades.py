import asyncio
import random
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from math_engine import (mines_multiplier, tower_multiplier,
                          generate_crash_point, keno_multiplier,
                          roulette_multiplier, apply_win_commission)
from utils.emoji import DOLLAR, WALLET, BET
from utils.user_state import get_bet

router = Router()


def _parse_uid(call: types.CallbackQuery) -> int:
    parts = call.data.split(":")
    if parts and parts[-1].isdigit() and len(parts[-1]) > 5:
        return int(parts[-1])
    return call.from_user.id


def _check_owner(call, uid) -> bool:
    return call.from_user.id == uid


async def _no(call):
    await call.answer("❌ Это не твоя игра!", show_alert=True)


# ============================================================
#                       МИНЫ
# ============================================================
@router.callback_query(F.data.startswith("mines_n:"))
async def mines_start(call: types.CallbackQuery):
    parts = call.data.split(":")
    mines = int(parts[1])
    uid = _parse_uid(call)
    if not _check_owner(call, uid):
        return await _no(call)

    bet = db.get_bet(uid)
    if not db.has_enough(uid, bet):
        return await call.answer("❌ Недостаточно средств", show_alert=True)

    db.update_balance(uid, -bet)
    db.add_wager(uid, bet)
    db.inc_games(uid)

    mine_positions = set(random.sample(range(25), mines))
    data = f"{mines}|{','.join(map(str, sorted(mine_positions)))}|"
    db.set_active_game(uid, "mines", "playing", bet, 1.0, data)

    await _render_mines(call.message, uid)
    await call.answer()


def _parse_mines(data):
    parts = data.split("|")
    mines = int(parts[0]) if parts[0] else 5
    mine_pos = set(map(int, parts[1].split(","))) if len(parts) > 1 and parts[1] else set()
    opened = set(map(int, parts[2].split(","))) if len(parts) > 2 and parts[2] else set()
    return mines, mine_pos, opened


def _mines_kb(opened, uid, mult, mine_pos=None, reveal=False):
    rows = []
    for r in range(5):
        row = []
        for c in range(5):
            i = r * 5 + c
            if reveal and mine_pos and i in mine_pos:
                row.append(InlineKeyboardButton(text="💣", callback_data=f"mnoop:{uid}"))
            elif i in opened:
                row.append(InlineKeyboardButton(text="💎", callback_data=f"mnoop:{uid}"))
            elif reveal:
                row.append(InlineKeyboardButton(text="⬜", callback_data=f"mnoop:{uid}"))
            else:
                row.append(InlineKeyboardButton(text="⬜", callback_data=f"mopen:{i}:{uid}"))
        rows.append(row)
    rows.append([InlineKeyboardButton(text=f"💰 Забрать {mult:.2f}x",
                                      callback_data=f"mcash:{uid}")])
    return rows


async def _render_mines(msg, uid):
    game = db.get_active_game(uid)
    if not game or game[0] != "mines":
        return
    _, _, bet, mult, data = game
    mines, mine_pos, opened = _parse_mines(data)
    rows = _mines_kb(opened, uid, mult)
    text = (f"💣 <b>Мины</b> ({mines} мин)\n"
            f"Открыто: <b>{len(opened)}</b> | Множитель: <b>{mult:.2f}x</b>\n"
            f"{BET} Ставка: <b>{bet}</b> {DOLLAR}")
    try:
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
                            parse_mode="HTML")
    except Exception:
        await msg.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
                         parse_mode="HTML")


@router.callback_query(F.data.startswith("mnoop:"))
async def mines_noop(call: types.CallbackQuery):
    await call.answer()


@router.callback_query(F.data.startswith("mopen:"))
async def mines_open(call: types.CallbackQuery):
    parts = call.data.split(":")
    idx = int(parts[1])
    uid = _parse_uid(call)
    if not _check_owner(call, uid):
        return await _no(call)

    game = db.get_active_game(uid)
    if not game or game[0] != "mines":
        return await call.answer("❌ Игра не найдена", show_alert=True)

    _, _, bet, mult, data = game
    mines, mine_pos, opened = _parse_mines(data)
    if idx in opened:
        return await call.answer()

    if idx in mine_pos:
        db.add_loss(uid, bet)
        db.add_game(uid, "mines", bet, 0, 0, "lose")
        db.delete_active_game(uid)
        rows = _mines_kb(opened, uid, mult, mine_pos, reveal=True)
        try:
            await call.message.edit_text(
                f"💥 <b>МИНА!</b>\nПотеряно: <b>{bet}</b> {DOLLAR}\n"
                f"{WALLET} Баланс: <b>{db.get_balance(uid):.2f}</b>",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
                parse_mode="HTML")
        except Exception:
            pass
        return await call.answer("💥 Мина!")

    opened.add(idx)
    new_mult = mines_multiplier(mines, len(opened))
    new_data = (f"{mines}|{','.join(map(str, sorted(mine_pos)))}|"
                f"{','.join(map(str, sorted(opened)))}")
    db.set_active_game(uid, "mines", "playing", bet, new_mult, new_data)
    await _render_mines(call.message, uid)
    await call.answer(f"💎 {new_mult:.2f}x")


@router.callback_query(F.data.startswith("mcash:"))
async def mines_cash(call: types.CallbackQuery):
    uid = _parse_uid(call)
    if not _check_owner(call, uid):
        return await _no(call)
    game = db.get_active_game(uid)
    if not game or game[0] != "mines":
        return await call.answer("❌", show_alert=True)
    _, _, bet, mult, data = game
    mines, mine_pos, opened = _parse_mines(data)
    if not opened:
        return await call.answer("❌ Открой ячейку!", show_alert=True)
    win = round(bet * mult, 2)
    credited, comm = apply_win_commission(win)
    db.update_balance(uid, credited)
    db.add_win(uid, credited)
    db.add_game(uid, "mines", bet, credited, mult, "win")

    from utils.refs import give_ref_bonus
    give_ref_bonus(uid, credited)

    db.delete_active_game(uid)
    await call.message.edit_text(
        f"💰 <b>Забрали!</b>\nМножитель: <b>{mult:.2f}x</b>\n"
        f"✅ +{credited:.2f} {DOLLAR}\n"
        f"💸 Комиссия 2%: <b>-{comm:.2f}</b> {DOLLAR}\n"
        f"{WALLET} Баланс: <b>{db.get_balance(uid):.2f}</b>",
        parse_mode="HTML")
    await call.answer("✅")


# ============================================================
#                       БАШНЯ
# ============================================================
@router.callback_query(F.data.startswith("ar:tower:"))
async def tower_start(call: types.CallbackQuery):
    uid = _parse_uid(call)
    if not _check_owner(call, uid):
        return await _no(call)

    bet = db.get_bet(uid)
    if not db.has_enough(uid, bet):
        return await call.answer("❌ Недостаточно средств", show_alert=True)
    db.update_balance(uid, -bet)
    db.add_wager(uid, bet)
    db.inc_games(uid)
    db.set_active_game(uid, "tower", "playing", bet, 1.0, "0")
    await _render_tower(call.message, uid)
    await call.answer()


async def _render_tower(msg, uid):
    game = db.get_active_game(uid)
    if not game or game[0] != "tower":
        return
    _, _, bet, mult, data = game
    level = int(data)
    rows = [[InlineKeyboardButton(text="⬆️ Подняться", callback_data=f"tup:{uid}")]]
    if level > 0:
        rows.append([InlineKeyboardButton(text=f"💰 Забрать {mult:.2f}x",
                                          callback_data=f"tcs:{uid}")])
    text = (f"🏰 <b>Башня</b>\nУровень: <b>{level}</b> | x{mult:.2f}\n"
            f"{BET} Ставка: <b>{bet}</b> {DOLLAR}")
    try:
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
                            parse_mode="HTML")
    except Exception:
        await msg.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
                         parse_mode="HTML")


@router.callback_query(F.data.startswith("tup:"))
async def tower_up(call: types.CallbackQuery):
    uid = _parse_uid(call)
    if not _check_owner(call, uid):
        return await _no(call)
    game = db.get_active_game(uid)
    if not game or game[0] != "tower":
        return await call.answer("❌", show_alert=True)
    _, _, bet, mult, data = game
    level = int(data)
    if random.random() < 0.7:
        new_level = level + 1
        new_mult = tower_multiplier(new_level)
        db.set_active_game(uid, "tower", "playing", bet, new_mult, str(new_level))
        await _render_tower(call.message, uid)
        await call.answer(f"✅ Уровень {new_level}!")
    else:
        db.add_loss(uid, bet)
        db.add_game(uid, "tower", bet, 0, 0, "lose")
        db.delete_active_game(uid)
        try:
            await call.message.edit_text(
                f"💥 Сорвался на уровне {level}!\n"
                f"Потеряно: <b>{bet}</b> {DOLLAR}\n"
                f"{WALLET} Баланс: <b>{db.get_balance(uid):.2f}</b>",
                parse_mode="HTML")
        except Exception:
            pass
        await call.answer("💥")


@router.callback_query(F.data.startswith("tcs:"))
async def tower_cash(call: types.CallbackQuery):
    uid = _parse_uid(call)
    if not _check_owner(call, uid):
        return await _no(call)
    game = db.get_active_game(uid)
    if not game or game[0] != "tower":
        return await call.answer("❌", show_alert=True)
    _, _, bet, mult, data = game
    level = int(data)
    if level <= 0:
        return await call.answer("❌ Сначала поднимись!", show_alert=True)
    win = round(bet * mult, 2)
    credited, comm = apply_win_commission(win)
    db.update_balance(uid, credited)
    db.add_win(uid, credited)
    db.add_game(uid, "tower", bet, credited, mult, "win")

    from utils.refs import give_ref_bonus
    give_ref_bonus(uid, credited)

    db.delete_active_game(uid)
    await call.message.edit_text(
        f"💰 <b>Забрали!</b>\nУровень: {level} | x{mult:.2f}\n"
        f"✅ +{credited:.2f} {DOLLAR}\n"
        f"💸 Комиссия 2%: <b>-{comm:.2f}</b> {DOLLAR}\n"
        f"{WALLET} Баланс: <b>{db.get_balance(uid):.2f}</b>",
        parse_mode="HTML")
    await call.answer("✅")


# ============================================================
#                       КРАШ
# ============================================================
@router.callback_query(F.data.startswith("ar:crash:"))
async def crash_start(call: types.CallbackQuery):
    uid = _parse_uid(call)
    if not _check_owner(call, uid):
        return await _no(call)
    bet = db.get_bet(uid)
    if not db.has_enough(uid, bet):
        return await call.answer("❌ Недостаточно", show_alert=True)
    db.update_balance(uid, -bet)
    db.add_wager(uid, bet)
    db.inc_games(uid)
    cp = generate_crash_point()
    db.set_active_game(uid, "crash", "playing", bet, 1.0, f"{cp}|1.0")
    msg = await call.message.edit_text(
        f"🚀 <b>Краш</b>\nМножитель: <b>1.00x</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💰 Забрать 1.00x",
                                  callback_data=f"ccs:{uid}")],
        ]), parse_mode="HTML")
    await call.answer()
    asyncio.create_task(_crash_loop(uid, msg, cp, bet))


async def _crash_loop(uid, msg, cp, bet):
    mult = 1.0
    while mult < cp and mult < 50:
        await asyncio.sleep(0.7)
        mult = round(mult + 0.05, 2)
        game = db.get_active_game(uid)
        if not game or game[0] != "crash":
            return
        db.set_active_game(uid, "crash", "playing", bet, mult, f"{cp}|{mult}")
        try:
            await msg.edit_text(
                f"🚀 <b>Краш</b>\nМножитель: <b>{mult:.2f}x</b>",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=f"💰 Забрать {mult:.2f}x",
                                          callback_data=f"ccs:{uid}")],
                ]), parse_mode="HTML")
        except Exception:
            pass
    game = db.get_active_game(uid)
    if not game or game[0] != "crash":
        return
    db.add_loss(uid, bet)
    db.add_game(uid, "crash", bet, 0, 0, "lose")
    db.delete_active_game(uid)
    try:
        await msg.edit_text(
            f"💥 <b>КРАШ на {cp:.2f}x!</b>\n"
            f"Потеряно: <b>{bet}</b> {DOLLAR}\n"
            f"{WALLET} Баланс: <b>{db.get_balance(uid):.2f}</b>",
            parse_mode="HTML")
    except Exception:
        pass


@router.callback_query(F.data.startswith("ccs:"))
async def crash_cash(call: types.CallbackQuery):
    uid = _parse_uid(call)
    if not _check_owner(call, uid):
        return await _no(call)
    game = db.get_active_game(uid)
    if not game or game[0] != "crash":
        return await call.answer("❌", show_alert=True)
    _, _, bet, mult, data = game
    parts = data.split("|")
    cp = float(parts[0])
    current = float(parts[1]) if len(parts) > 1 else 1.0
    if current >= cp:
        db.add_loss(uid, bet)
        db.add_game(uid, "crash", bet, 0, 0, "lose")
        db.delete_active_game(uid)
        return await call.answer("💥 Уже краш!", show_alert=True)
    win = round(bet * current, 2)
    credited, comm = apply_win_commission(win)
    db.update_balance(uid, credited)
    db.add_win(uid, credited)
    db.add_game(uid, "crash", bet, credited, current, "win")

    from utils.refs import give_ref_bonus
    give_ref_bonus(uid, credited)

    db.delete_active_game(uid)
    await call.message.edit_text(
        f"💰 <b>Забрали на {current:.2f}x!</b>\n"
        f"✅ +{credited:.2f} {DOLLAR}\n"
        f"💸 Комиссия 2%: <b>-{comm:.2f}</b> {DOLLAR}\n"
        f"{WALLET} Баланс: <b>{db.get_balance(uid):.2f}</b>",
        parse_mode="HTML")
    await call.answer("✅")


# ============================================================
#                       КЕНО
# ============================================================
@router.callback_query(F.data.startswith("ar:keno:"))
async def keno_start(call: types.CallbackQuery):
    uid = _parse_uid(call)
    if not _check_owner(call, uid):
        return await _no(call)
    bet = db.get_bet(uid)
    if not db.has_enough(uid, bet):
        return await call.answer("❌ Недостаточно", show_alert=True)
    db.update_balance(uid, -bet)
    db.add_wager(uid, bet)
    db.inc_games(uid)
    hits = random.randint(0, 5)
    mult = keno_multiplier(hits, 5)
    win = round(bet * mult, 2)
    if mult > 0:
        credited, comm = apply_win_commission(win)
        db.update_balance(uid, credited)
        db.add_win(uid, credited)
        db.add_game(uid, "keno", bet, credited, mult, "win")

        from utils.refs import give_ref_bonus
        give_ref_bonus(uid, credited)

        await call.message.edit_text(
            f"🎯 <b>Кено</b>\nУгадано: <b>{hits}</b>/5\n"
            f"✅ x{mult:.2f} → <b>+{credited:.2f}</b> {DOLLAR}\n"
            f"💸 Комиссия 2%: <b>-{comm:.2f}</b> {DOLLAR}\n"
            f"{WALLET} Баланс: <b>{db.get_balance(uid):.2f}</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎮 Меню игр",
                                      callback_data="games_main", style="primary")],
            ]), parse_mode="HTML")
    else:
        db.add_loss(uid, bet)
        db.add_game(uid, "keno", bet, 0, 0, "lose")
        await call.message.edit_text(
            f"🎯 <b>Кено</b>\nУгадано: <b>{hits}</b>/5\n"
            f"❌ -{bet:.2f} {DOLLAR}\n"
            f"{WALLET} Баланс: <b>{db.get_balance(uid):.2f}</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎮 Меню игр",
                                      callback_data="games_main", style="primary")],
            ]), parse_mode="HTML")
    await call.answer()


# ============================================================
#                       РУЛЕТКА
# ============================================================
@router.callback_query(F.data.startswith("ar:roulette:"))
async def roulette_start(call: types.CallbackQuery):
    uid = _parse_uid(call)
    if not _check_owner(call, uid):
        return await _no(call)
    bet = db.get_bet(uid)
    if not db.has_enough(uid, bet):
        return await call.answer("❌ Недостаточно", show_alert=True)
    db.update_balance(uid, -bet)
    db.add_wager(uid, bet)
    db.inc_games(uid)
    n = random.randint(0, 36)
    reds = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
    color = "green" if n == 0 else ("red" if n in reds else "black")
    win, result = roulette_multiplier(bet, "red", n, color)
    ci = {"red":"🔴","black":"⚫","green":"🟢"}[color]
    if result == "win":
        credited, comm = apply_win_commission(win)
        db.update_balance(uid, credited)
        db.add_win(uid, credited)
        db.add_game(uid, "roulette", bet, credited, 2.0, "win")

        from utils.refs import give_ref_bonus
        give_ref_bonus(uid, credited)

        await call.message.edit_text(
            f"🎡 <b>Рулетка</b>\nВыпало {ci} <b>{n}</b>\n"
            f"✅ +{credited:.2f} {DOLLAR}\n"
            f"💸 Комиссия 2%: <b>-{comm:.2f}</b> {DOLLAR}\n"
            f"{WALLET} Баланс: <b>{db.get_balance(uid):.2f}</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎮 Меню игр",
                                      callback_data="games_main", style="primary")],
            ]), parse_mode="HTML")
    else:
        db.add_loss(uid, bet)
        db.add_game(uid, "roulette", bet, 0, 0, "lose")
        await call.message.edit_text(
            f"🎡 <b>Рулетка</b>\nВыпало {ci} <b>{n}</b>\n"
            f"❌ -{bet:.2f} {DOLLAR}\n"
            f"{WALLET} Баланс: <b>{db.get_balance(uid):.2f}</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎮 Меню игр",
                                      callback_data="games_main", style="primary")],
            ]), parse_mode="HTML")
    await call.answer()


# ============================================================
#              ПРЯМОЙ ЗАПУСК АРКАД
# ============================================================
async def start_crash_direct(message, uid, bet):
    db.update_balance(uid, -bet)
    db.add_wager(uid, bet)
    db.inc_games(uid)
    cp = generate_crash_point()
    db.set_active_game(uid, "crash", "playing", bet, 1.0, f"{cp}|1.0")
    msg = await message.answer(
        f"🚀 <b>Краш</b>\nМножитель: <b>1.00x</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💰 Забрать 1.00x",
                                  callback_data=f"ccs:{uid}")],
        ]), parse_mode="HTML")
    asyncio.create_task(_crash_loop(uid, msg, cp, bet))


async def play_keno_direct(message, uid, bet):
    db.update_balance(uid, -bet)
    db.add_wager(uid, bet)
    db.inc_games(uid)
    hits = random.randint(0, 5)
    mult = keno_multiplier(hits, 5)
    win = round(bet * mult, 2)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Меню игр", callback_data="games_main",
                              style="primary")],
    ])
    if mult > 0:
        credited, comm = apply_win_commission(win)
        db.update_balance(uid, credited)
        db.add_win(uid, credited)
        db.add_game(uid, "keno", bet, credited, mult, "win")
        from utils.refs import give_ref_bonus
        give_ref_bonus(uid, credited)
        await message.answer(
            f"🎯 Кено\nУгадано: {hits}/5\n✅ +{credited:.2f} {DOLLAR}\n"
            f"💸 Комиссия 2%: <b>-{comm:.2f}</b> {DOLLAR}\n"
            f"Баланс: <b>{db.get_balance(uid):.2f}</b>",
            reply_markup=kb, parse_mode="HTML")
    else:
        db.add_loss(uid, bet)
        db.add_game(uid, "keno", bet, 0, 0, "lose")
        await message.answer(
            f"🎯 Кено\nУгадано: {hits}/5\n❌ -{bet:.2f} {DOLLAR}\n"
            f"Баланс: <b>{db.get_balance(uid):.2f}</b>",
            reply_markup=kb, parse_mode="HTML")


async def play_roulette_direct(message, uid, bet):
    db.update_balance(uid, -bet)
    db.add_wager(uid, bet)
    db.inc_games(uid)
    n = random.randint(0, 36)
    reds = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
    color = "green" if n == 0 else ("red" if n in reds else "black")
    win, result = roulette_multiplier(bet, "red", n, color)
    ci = {"red":"🔴","black":"⚫","green":"🟢"}[color]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Меню игр", callback_data="games_main",
                              style="primary")],
    ])
    if result == "win":
        credited, comm = apply_win_commission(win)
        db.update_balance(uid, credited)
        db.add_win(uid, credited)
        db.add_game(uid, "roulette", bet, credited, 2.0, "win")
        from utils.refs import give_ref_bonus
        give_ref_bonus(uid, credited)
        await message.answer(
            f"🎡 Рулетка\nВыпало {ci} <b>{n}</b>\n✅ +{credited:.2f} {DOLLAR}\n"
            f"💸 Комиссия 2%: <b>-{comm:.2f}</b> {DOLLAR}\n"
            f"Баланс: <b>{db.get_balance(uid):.2f}</b>",
            reply_markup=kb, parse_mode="HTML")
    else:
        db.add_loss(uid, bet)
        db.add_game(uid, "roulette", bet, 0, 0, "lose")
        await message.answer(
            f"🎡 Рулетка\nВыпало {ci} <b>{n}</b>\n❌ -{bet:.2f} {DOLLAR}\n"
            f"Баланс: <b>{db.get_balance(uid):.2f}</b>",
            reply_markup=kb, parse_mode="HTML")