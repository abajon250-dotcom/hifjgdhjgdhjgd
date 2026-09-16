import asyncio
import os
import random
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.enums import ChatType
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from math_engine import (calc_1_dice, calc_2_dice, calc_3_dice,
                          calc_football, calc_basketball, calc_darts, calc_bowling,
                          spin_slots, calc_slots,
                          mines_multiplier, tower_multiplier,
                          generate_crash_point, keno_multiplier, roulette_multiplier)
from utils.emoji import DOLLAR, WALLET, BET

router = Router()
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

GROUP_FILTER = F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP})


def _check_owner(call: types.CallbackQuery, owner_uid: int) -> bool:
    return call.from_user.id == owner_uid


async def _not_owner(call: types.CallbackQuery):
    await call.answer("❌ Это не твоя игра! Напиши свою команду.", show_alert=True)


# ============================================================
#              ИНФО-КОМАНДЫ
# ============================================================
@router.message(GROUP_FILTER, Command("balance", "bal", "баланс", "бал"))
@router.message(GROUP_FILTER, F.text.regexp(r"(?i)^(баланс|бал)$"))
async def group_balance(message: types.Message):
    if not message.from_user:
        return
    uid = message.from_user.id
    db.get_user(uid)
    await message.reply(
        f"{DOLLAR} <a href='tg://user?id={uid}'>{message.from_user.full_name}</a> — "
        f"баланс: <b>{db.get_balance(uid):.2f}</b>",
        parse_mode="HTML"
    )


@router.message(GROUP_FILTER, Command("top", "топ"))
@router.message(GROUP_FILTER, F.text.regexp(r"(?i)^топ$"))
async def group_top(message: types.Message):
    top = db.get_top_wagered(5)
    if not top:
        return await message.reply("Пусто.")
    text = "🏆 <b>Топ-5 по обороту:</b>\n\n"
    for i, (uid, uname, wag) in enumerate(top, 1):
        text += (f"{i}. <a href='tg://user?id={uid}'>"
                 f"{uname or uid}</a> — <b>{wag:.2f}</b>\n")
    await message.reply(text, parse_mode="HTML", disable_web_page_preview=True)


@router.message(GROUP_FILTER, Command("stats", "стата", "профиль", "статистика"))
@router.message(GROUP_FILTER, F.text.regexp(r"(?i)^(стата|профиль|статистика)$"))
async def group_stats(message: types.Message):
    if not message.from_user:
        return
    uid = message.from_user.id
    s = db.get_stats(uid)
    await message.reply(
        f"📊 <a href='tg://user?id={uid}'>{message.from_user.full_name}</a>\n"
        f"{DOLLAR} {s['balance']:.2f} | 📉 {s['total_wagered']:.2f} | "
        f"🎲 {s['games_played']}",
        parse_mode="HTML"
    )


@router.message(GROUP_FILTER, Command("help", "помощь", "хелп"))
@router.message(GROUP_FILTER, F.text.regexp(r"(?i)^(помощь|хелп)$"))
async def group_help(message: types.Message):
    await message.reply(
        "⚙️ <b>Команды в чате:</b>\n\n"
        "📊 <b>Инфо:</b>\n"
        "• <code>баланс</code> — мой баланс\n"
        "• <code>топ</code> — топ-5 игроков\n"
        "• <code>стата</code> — моя статистика\n\n"
        "🎮 <b>Игры:</b>\n"
        "• <code>игры</code> — меню игр\n"
        "• <code>куб</code> — кубики\n"
        "• <code>футбол</code> / <code>баскет</code> / <code>дартс</code> / <code>боулинг</code>\n"
        "• <code>слоты</code>\n"
        "• <code>мины</code> / <code>башня</code> / <code>краш</code> / <code>кено</code> / <code>рулетка</code>\n\n"
        "🔒 Деньги списываются только с того, кто запустил игру.",
        parse_mode="HTML"
    )


# ============================================================
#              МЕНЮ ИГР
# ============================================================
@router.message(GROUP_FILTER, Command("games", "игры", "играть"))
@router.message(GROUP_FILTER, F.text.regexp(r"(?i)^(игры|играть)$"))
async def group_games_menu(message: types.Message):
    if not message.from_user:
        return
    uid = message.from_user.id
    db.get_user(uid)
    bet = db.get_bet(uid)
    bal = db.get_balance(uid)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Куб", callback_data=f"g:menu:dice:{uid}"),
         InlineKeyboardButton(text="⚽ Футбол", callback_data=f"g:menu:football:{uid}")],
        [InlineKeyboardButton(text="🏀 Баскет", callback_data=f"g:menu:basket:{uid}"),
         InlineKeyboardButton(text="🎯 Дартс", callback_data=f"g:menu:darts:{uid}")],
        [InlineKeyboardButton(text="🎳 Боулинг", callback_data=f"g:menu:bowling:{uid}"),
         InlineKeyboardButton(text="🎰 Слоты", callback_data=f"g:menu:slots:{uid}")],
        [InlineKeyboardButton(text="💣 Мины", callback_data=f"g:menu:mines:{uid}"),
         InlineKeyboardButton(text="🏰 Башня", callback_data=f"g:menu:tower:{uid}")],
        [InlineKeyboardButton(text="🚀 Краш", callback_data=f"g:menu:crash:{uid}"),
         InlineKeyboardButton(text="🎯 Кено", callback_data=f"g:menu:keno:{uid}")],
        [InlineKeyboardButton(text="🎡 Рулетка", callback_data=f"g:menu:roulette:{uid}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"g:cancel:{uid}",
                              style="danger")],
    ])
    await message.reply(
        f"🎮 <a href='tg://user?id={uid}'>{message.from_user.full_name}</a>, "
        f"выбирай игру!\n\n"
        f"{BET} Ставка: <b>{bet}</b> {DOLLAR}\n"
        f"{WALLET} Баланс: <b>{bal:.2f}</b> {DOLLAR}",
        reply_markup=kb, parse_mode="HTML"
    )


# ============================================================
#              МЕНЮ → ВЫБОР ИГРЫ
# ============================================================
@router.callback_query(F.data.startswith("g:menu:"))
async def group_menu_choice(call: types.CallbackQuery):
    parts = call.data.split(":")
    game = parts[2]
    owner_uid = int(parts[3])

    if not _check_owner(call, owner_uid):
        return await _not_owner(call)

    uid = call.from_user.id
    bet = db.get_bet(uid)

    if not db.has_enough(uid, bet):
        return await call.answer("❌ Недостаточно средств", show_alert=True)

    # ---------- КУБИКИ ----------
    if game == "dice":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎲 1 Куб", callback_data=f"g:dice1:{uid}"),
             InlineKeyboardButton(text="🎲 2 Куба", callback_data=f"g:dice2:{uid}")],
            [InlineKeyboardButton(text="🎲 3 Куба", callback_data=f"g:dice3:{uid}")],
            [InlineKeyboardButton(text="Назад", callback_data=f"g:games_back:{uid}",
                                  style="primary")],
        ])
        await call.message.edit_text(
            f"🎲 <b>Кубики</b>\n{BET} Ставка: <b>{bet}</b> {DOLLAR}\n\nВыбери режим:",
            reply_markup=kb, parse_mode="HTML"
        )

    # ---------- ФУТБОЛ ----------
    elif game == "football":
        await _show_sport_menu(call, uid, bet, "fc",
            "⚽ <b>Футбол</b>",
            [("Мимо (x3)", "mimo"), ("Штанга (x4)", "shtanga"),
             ("Центр (x2)", "center"), ("От штанги (x3.5)", "from_shtanga"),
             ("Угол (x1.8)", "corner")])

    # ---------- БАСКЕТ ----------
    elif game == "basket":
        await _show_sport_menu(call, uid, bet, "bc",
            "🏀 <b>Баскетбол</b>",
            [("Отскок (x3)", "otskok"), ("Близко (x4)", "blizko"),
             ("Застрял (x5)", "zastryal"), ("С краем (x2)", "edge"),
             ("Прямое (x1.5)", "direct")])

    # ---------- ДАРТС ----------
    elif game == "darts":
        await _show_sport_menu(call, uid, bet, "dc",
            "🎯 <b>Дартс</b>",
            [("Промах (x3)", "miss"), ("В центр (x5)", "bull"),
             ("Сектор 3", "s3"), ("Сектор 4", "s4"),
             ("Сектор 5", "s5"), ("Сектор 6", "s6")])

    # ---------- БОУЛИНГ ----------
    elif game == "bowling":
        await _show_sport_menu(call, uid, bet, "wc",
            "🎳 <b>Боулинг</b>",
            [("Промах (x3.5)", "miss"), ("1/6 (x4)", "p1"),
             ("3/6 (x3)", "p3"), ("4/6 (x2.5)", "p4"),
             ("5/6 (x2)", "p5"), ("Страйк (x1.5)", "strike")])

    # ---------- СЛОТЫ ----------
    elif game == "slots":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="777 (x60)", callback_data=f"g:sl:777:{uid}")],
            [InlineKeyboardButton(text="77* (x15)", callback_data=f"g:sl:77x:{uid}")],
            [InlineKeyboardButton(text="Любая комбинация", callback_data=f"g:sl:any:{uid}")],
            [InlineKeyboardButton(text="Дубль (x3)", callback_data=f"g:sl:double:{uid}")],
            [InlineKeyboardButton(text="Назад", callback_data=f"g:games_back:{uid}",
                                  style="primary")],
        ])
        await call.message.edit_text(
            f"🎰 <b>Слоты</b>\n{BET} Ставка: <b>{bet}</b> {DOLLAR}\n\nВыбери режим:",
            reply_markup=kb, parse_mode="HTML"
        )

    # ---------- МИНЫ ----------
    elif game == "mines":
        rows, row = [], []
        for i in range(1, 25):
            row.append(InlineKeyboardButton(text=str(i), callback_data=f"g:mines:{i}:{uid}"))
            if len(row) == 6:
                rows.append(row); row = []
        if row:
            rows.append(row)
        rows.append([InlineKeyboardButton(text="Назад", callback_data=f"g:games_back:{uid}",
                                          style="primary")])
        await call.message.edit_text(
            f"💣 <b>Мины</b>\n{BET} Ставка: <b>{bet}</b> {DOLLAR}\n\n"
            f"Выбери количество мин:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=rows), parse_mode="HTML"
        )

    # ---------- БАШНЯ ----------
    elif game == "tower":
        db.update_balance(uid, -bet)
        db.add_wager(uid, bet)
        db.inc_games(uid)
        db.set_active_game(uid, "tower", "playing", bet, 1.0, "0")
        await _render_tower_group(call.message, uid)

    # ---------- КРАШ ----------
    elif game == "crash":
        db.update_balance(uid, -bet)
        db.add_wager(uid, bet)
        db.inc_games(uid)
        crash_point = generate_crash_point()
        db.set_active_game(uid, "crash", "playing", bet, 1.0,
                           f"{crash_point}|1.0")
        msg = await call.message.edit_text(
            f"🚀 <b>Краш</b>\n{BET} Ставка: <b>{bet}</b> {DOLLAR}\n"
            f"Множитель: <b>1.00x</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"💰 Забрать 1.00x",
                                      callback_data=f"g:crash_cash:{uid}")],
            ]), parse_mode="HTML")
        asyncio.create_task(_crash_loop_group(uid, msg, crash_point, bet))

    # ---------- КЕНО ----------
    elif game == "keno":
        db.update_balance(uid, -bet)
        db.add_wager(uid, bet)
        db.inc_games(uid)
        hits = random.randint(0, 5)
        mult = keno_multiplier(hits, 5)
        win = round(bet * mult, 2)
        if mult > 0:
            db.update_balance(uid, win)
            db.add_win(uid, win)
            db.add_game(uid, "keno", bet, win, mult, "win")
            await call.message.edit_text(
                f"🎯 <b>Кено</b>\nУгадано: <b>{hits}</b>/5\n"
                f"✅ x{mult:.2f} → <b>+{win:.2f}</b> {DOLLAR}\n"
                f"{WALLET} Баланс: <b>{db.get_balance(uid):.2f}</b>",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔁 Ещё", callback_data=f"g:menu:keno:{uid}")],
                    [InlineKeyboardButton(text="Назад", callback_data=f"g:games_back:{uid}",
                                          style="primary")],
                ]), parse_mode="HTML")
        else:
            db.add_loss(uid, bet)
            db.add_game(uid, "keno", bet, 0, 0, "lose")
            await call.message.edit_text(
                f"🎯 <b>Кено</b>\nУгадано: <b>{hits}</b>/5\n"
                f"❌ -{bet:.2f} {DOLLAR}\n"
                f"{WALLET} Баланс: <b>{db.get_balance(uid):.2f}</b>",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔁 Ещё", callback_data=f"g:menu:keno:{uid}")],
                    [InlineKeyboardButton(text="Назад", callback_data=f"g:games_back:{uid}",
                                          style="primary")],
                ]), parse_mode="HTML")

    # ---------- РУЛЕТКА ----------
    elif game == "roulette":
        db.update_balance(uid, -bet)
        db.add_wager(uid, bet)
        db.inc_games(uid)
        number = random.randint(0, 36)
        reds = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
        color = "green" if number == 0 else ("red" if number in reds else "black")
        win, result = roulette_multiplier(bet, "red", number, color)
        color_emoji = {"red": "🔴", "black": "⚫", "green": "🟢"}[color]
        if result == "win":
            db.update_balance(uid, win)
            db.add_win(uid, win)
            db.add_game(uid, "roulette", bet, win, 2.0, "win")
            await call.message.edit_text(
                f"🎡 <b>Рулетка</b>\nВыпало: {color_emoji} <b>{number}</b>\n"
                f"✅ +{win:.2f} {DOLLAR}\n"
                f"{WALLET} Баланс: <b>{db.get_balance(uid):.2f}</b>",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔁 Ещё", callback_data=f"g:menu:roulette:{uid}")],
                    [InlineKeyboardButton(text="Назад", callback_data=f"g:games_back:{uid}",
                                          style="primary")],
                ]), parse_mode="HTML")
        else:
            db.add_loss(uid, bet)
            db.add_game(uid, "roulette", bet, 0, 0, "lose")
            await call.message.edit_text(
                f"🎡 <b>Рулетка</b>\nВыпало: {color_emoji} <b>{number}</b>\n"
                f"❌ -{bet:.2f} {DOLLAR}\n"
                f"{WALLET} Баланс: <b>{db.get_balance(uid):.2f}</b>",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔁 Ещё", callback_data=f"g:menu:roulette:{uid}")],
                    [InlineKeyboardButton(text="Назад", callback_data=f"g:games_back:{uid}",
                                          style="primary")],
                ]), parse_mode="HTML")

    await call.answer()


async def _show_sport_menu(call, uid, bet, prefix, title, items):
    rows, row = [], []
    for text, code in items:
        row.append(InlineKeyboardButton(text=text,
                                        callback_data=f"g:{prefix}:{code}:{uid}"))
        if len(row) == 2:
            rows.append(row); row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="Назад",
                                      callback_data=f"g:games_back:{uid}",
                                      style="primary")])
    await call.message.edit_text(
        f"{title}\n{BET} Ставка: <b>{bet}</b> {DOLLAR}\n\nВыбери исход:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("g:games_back:"))
async def group_games_back(call: types.CallbackQuery):
    owner_uid = int(call.data.split(":")[2])
    if not _check_owner(call, owner_uid):
        return await _not_owner(call)

    uid = call.from_user.id
    bet = db.get_bet(uid)
    bal = db.get_balance(uid)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Куб", callback_data=f"g:menu:dice:{uid}"),
         InlineKeyboardButton(text="⚽ Футбол", callback_data=f"g:menu:football:{uid}")],
        [InlineKeyboardButton(text="🏀 Баскет", callback_data=f"g:menu:basket:{uid}"),
         InlineKeyboardButton(text="🎯 Дартс", callback_data=f"g:menu:darts:{uid}")],
        [InlineKeyboardButton(text="🎳 Боулинг", callback_data=f"g:menu:bowling:{uid}"),
         InlineKeyboardButton(text="🎰 Слоты", callback_data=f"g:menu:slots:{uid}")],
        [InlineKeyboardButton(text="💣 Мины", callback_data=f"g:menu:mines:{uid}"),
         InlineKeyboardButton(text="🏰 Башня", callback_data=f"g:menu:tower:{uid}")],
        [InlineKeyboardButton(text="🚀 Краш", callback_data=f"g:menu:crash:{uid}"),
         InlineKeyboardButton(text="🎯 Кено", callback_data=f"g:menu:keno:{uid}")],
        [InlineKeyboardButton(text="🎡 Рулетка", callback_data=f"g:menu:roulette:{uid}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"g:cancel:{uid}",
                              style="danger")],
    ])
    await call.message.edit_text(
        f"🎮 <a href='tg://user?id={uid}'>{call.from_user.full_name}</a>, "
        f"выбирай игру!\n\n"
        f"{BET} Ставка: <b>{bet}</b> {DOLLAR}\n"
        f"{WALLET} Баланс: <b>{bal:.2f}</b> {DOLLAR}",
        reply_markup=kb, parse_mode="HTML"
    )
    await call.answer()


# ============================================================
#              ОТМЕНА
# ============================================================
@router.callback_query(F.data.startswith("g:cancel:"))
async def group_cancel(call: types.CallbackQuery):
    owner_uid = int(call.data.split(":")[2])
    if not _check_owner(call, owner_uid):
        return await _not_owner(call)
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.answer("Отменено")


# ============================================================
#              КУБИК — 1/2/3
# ============================================================
@router.callback_query(F.data.startswith("g:dice1:"))
async def g_dice1_menu(call: types.CallbackQuery):
    uid = int(call.data.split(":")[2])
    if not _check_owner(call, uid):
        return await _not_owner(call)
    bet = db.get_bet(uid)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Чёт (x1.9)", callback_data=f"g:d1:even:{uid}"),
         InlineKeyboardButton(text="Нечёт (x1.9)", callback_data=f"g:d1:odd:{uid}")],
        [InlineKeyboardButton(text="Меньше (x1.9)", callback_data=f"g:d1:less:{uid}"),
         InlineKeyboardButton(text="Больше (x1.9)", callback_data=f"g:d1:more:{uid}")],
        [InlineKeyboardButton(text="1", callback_data=f"g:d1:num1:{uid}"),
         InlineKeyboardButton(text="2", callback_data=f"g:d1:num2:{uid}"),
         InlineKeyboardButton(text="3", callback_data=f"g:d1:num3:{uid}")],
        [InlineKeyboardButton(text="4", callback_data=f"g:d1:num4:{uid}"),
         InlineKeyboardButton(text="5", callback_data=f"g:d1:num5:{uid}"),
         InlineKeyboardButton(text="6", callback_data=f"g:d1:num6:{uid}")],
        [InlineKeyboardButton(text="Назад", callback_data=f"g:menu:dice:{uid}",
                              style="primary")],
    ])
    await call.message.edit_text(
        f"🎲 <b>1 Куб</b>\n{BET} Ставка: <b>{bet}</b> {DOLLAR}\n\nВыбери исход:",
        reply_markup=kb, parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("g:dice2:"))
async def g_dice2_menu(call: types.CallbackQuery):
    uid = int(call.data.split(":")[2])
    if not _check_owner(call, uid):
        return await _not_owner(call)
    bet = db.get_bet(uid)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Чёт (x3.8)", callback_data=f"g:d2:even:{uid}"),
         InlineKeyboardButton(text="Нечет (x3.8)", callback_data=f"g:d2:odd:{uid}")],
        [InlineKeyboardButton(text="Больше 7", callback_data=f"g:d2:more:{uid}"),
         InlineKeyboardButton(text="Меньше 7", callback_data=f"g:d2:less:{uid}")],
        [InlineKeyboardButton(text="Дубль (x5.5)", callback_data=f"g:d2:double:{uid}")],
        [InlineKeyboardButton(text="Назад", callback_data=f"g:menu:dice:{uid}",
                              style="primary")],
    ])
    await call.message.edit_text(
        f"🎲 <b>2 Куба</b>\n{BET} Ставка: <b>{bet}</b> {DOLLAR}\n\nВыбери исход:",
        reply_markup=kb, parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("g:dice3:"))
async def g_dice3_menu(call: types.CallbackQuery):
    uid = int(call.data.split(":")[2])
    if not _check_owner(call, uid):
        return await _not_owner(call)
    bet = db.get_bet(uid)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Три Чёт (x7.5)", callback_data=f"g:d3:three_even:{uid}"),
         InlineKeyboardButton(text="Три Нечет (x7.5)", callback_data=f"g:d3:three_odd:{uid}")],
        [InlineKeyboardButton(text="Трипл (x33)", callback_data=f"g:d3:triple:{uid}")],
        [InlineKeyboardButton(text="Уникальные (x6)", callback_data=f"g:d3:unique:{uid}")],
        [InlineKeyboardButton(text="Назад", callback_data=f"g:menu:dice:{uid}",
                              style="primary")],
    ])
    await call.message.edit_text(
        f"🎲 <b>3 Куба</b>\n{BET} Ставка: <b>{bet}</b> {DOLLAR}\n\nВыбери исход:",
        reply_markup=kb, parse_mode="HTML")
    await call.answer()


# ============================================================
#              ИГРА — 1 КУБ
# ============================================================
@router.callback_query(F.data.startswith("g:d1:"))
async def g_d1_play(call: types.CallbackQuery):
    parts = call.data.split(":")
    choice = parts[2]
    uid = int(parts[3])
    if not _check_owner(call, uid):
        return await _not_owner(call)

    bet = db.get_bet(uid)
    if not db.has_enough(uid, bet):
        return await call.answer("❌ Недостаточно средств", show_alert=True)

    db.update_balance(uid, -bet)
    db.add_wager(uid, bet)
    db.inc_games(uid)

    await call.message.edit_text(f"🎲 Бросаю... Ставка: <b>{bet}</b> {DOLLAR}",
                                 parse_mode="HTML")
    await call.answer()

    m = await call.message.answer_dice(emoji="🎲")
    await asyncio.sleep(3.5)
    v = m.dice.value
    win, result = calc_1_dice(bet, choice, v)

    await _finish_group(call, uid, "dice_1", "🎲", v, bet, win, result, 2.0)


# ============================================================
#              ИГРА — 2 КУБА
# ============================================================
@router.callback_query(F.data.startswith("g:d2:"))
async def g_d2_play(call: types.CallbackQuery):
    parts = call.data.split(":")
    choice = parts[2]
    uid = int(parts[3])
    if not _check_owner(call, uid):
        return await _not_owner(call)

    bet = db.get_bet(uid)
    if not db.has_enough(uid, bet):
        return await call.answer("❌ Недостаточно", show_alert=True)

    db.update_balance(uid, -bet)
    db.add_wager(uid, bet)
    db.inc_games(uid)

    await call.message.edit_text(f"🎲🎲 Бросаю... Ставка: <b>{bet}</b> {DOLLAR}",
                                 parse_mode="HTML")
    await call.answer()

    m1 = await call.message.answer_dice(emoji="🎲")
    await asyncio.sleep(3.5)
    m2 = await call.message.answer_dice(emoji="🎲")
    await asyncio.sleep(3.5)
    v1, v2 = m1.dice.value, m2.dice.value
    win, result = calc_2_dice(bet, choice, v1, v2)

    await _finish_group(call, uid, "dice_2", f"🎲 {v1}+{v2}", v1 + v2,
                        bet, win, result, win / bet if bet else 0)


# ============================================================
#              ИГРА — 3 КУБА
# ============================================================
@router.callback_query(F.data.startswith("g:d3:"))
async def g_d3_play(call: types.CallbackQuery):
    parts = call.data.split(":")
    choice = parts[2]
    uid = int(parts[3])
    if not _check_owner(call, uid):
        return await _not_owner(call)

    bet = db.get_bet(uid)
    if not db.has_enough(uid, bet):
        return await call.answer("❌ Недостаточно", show_alert=True)

    db.update_balance(uid, -bet)
    db.add_wager(uid, bet)
    db.inc_games(uid)

    await call.message.edit_text(f"🎲🎲🎲 Бросаю... Ставка: <b>{bet}</b> {DOLLAR}",
                                 parse_mode="HTML")
    await call.answer()

    m1 = await call.message.answer_dice(emoji="🎲")
    await asyncio.sleep(3.5)
    m2 = await call.message.answer_dice(emoji="🎲")
    await asyncio.sleep(3.5)
    m3 = await call.message.answer_dice(emoji="🎲")
    await asyncio.sleep(3.5)
    v1, v2, v3 = m1.dice.value, m2.dice.value, m3.dice.value
    win, result = calc_3_dice(bet, choice, v1, v2, v3)

    await _finish_group(call, uid, "dice_3", f"🎲 {v1}+{v2}+{v3}", v1+v2+v3,
                        bet, win, result, win / bet if bet else 0)


# ============================================================
#              ИГРА — СПОРТ
# ============================================================
@router.callback_query(F.data.startswith("g:fc:"))
async def g_football(call: types.CallbackQuery):
    await _sport_group(call, "football", "⚽", calc_football)


@router.callback_query(F.data.startswith("g:bc:"))
async def g_basket(call: types.CallbackQuery):
    await _sport_group(call, "basketball", "🏀", calc_basketball)


@router.callback_query(F.data.startswith("g:dc:"))
async def g_darts(call: types.CallbackQuery):
    await _sport_group(call, "darts", "🎯", calc_darts)


@router.callback_query(F.data.startswith("g:wc:"))
async def g_bowling(call: types.CallbackQuery):
    await _sport_group(call, "bowling", "🎳", calc_bowling)


async def _sport_group(call: types.CallbackQuery, game: str, emoji: str, calc_fn):
    parts = call.data.split(":")
    choice = parts[2]
    uid = int(parts[3])
    if not _check_owner(call, uid):
        return await _not_owner(call)

    bet = db.get_bet(uid)
    if not db.has_enough(uid, bet):
        return await call.answer("❌ Недостаточно", show_alert=True)

    db.update_balance(uid, -bet)
    db.add_wager(uid, bet)
    db.inc_games(uid)

    await call.message.edit_text(f"{emoji} Играем... Ставка: <b>{bet}</b> {DOLLAR}",
                                 parse_mode="HTML")
    await call.answer()

    m = await call.message.answer_dice(emoji=emoji)
    await asyncio.sleep(3.5)
    v = m.dice.value
    win, result = calc_fn(bet, choice, v)

    await _finish_group(call, uid, f"sport_{game}", emoji, v,
                        bet, win, result, win / bet if bet else 0)


# ============================================================
#              ИГРА — СЛОТЫ
# ============================================================
@router.callback_query(F.data.startswith("g:sl:"))
async def g_slots(call: types.CallbackQuery):
    parts = call.data.split(":")
    choice = parts[2]
    uid = int(parts[3])
    if not _check_owner(call, uid):
        return await _not_owner(call)

    bet = db.get_bet(uid)
    if not db.has_enough(uid, bet):
        return await call.answer("❌ Недостаточно", show_alert=True)

    db.update_balance(uid, -bet)
    db.add_wager(uid, bet)
    db.inc_games(uid)

    SYMBOLS = ["7️⃣", "🍇", "🍋", "BAR"]
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

    await _finish_group(call, uid, "slots", reels_str, reels_str,
                        bet, win, result, win / bet if bet else 0)


# ============================================================
#              МИНЫ
# ============================================================
@router.callback_query(F.data.startswith("g:mines:"))
async def g_mines_start(call: types.CallbackQuery):
    parts = call.data.split(":")
    mines = int(parts[2])
    uid = int(parts[3])
    if not _check_owner(call, uid):
        return await _not_owner(call)

    bet = db.get_bet(uid)
    if not db.has_enough(uid, bet):
        return await call.answer("❌ Недостаточно", show_alert=True)

    db.update_balance(uid, -bet)
    db.add_wager(uid, bet)
    db.inc_games(uid)

    mine_positions = set(random.sample(range(25), mines))
    data = f"{mines}|{','.join(map(str, sorted(mine_positions)))}|"
    db.set_active_game(uid, "mines", "playing", bet, 1.0, data)

    await _render_mines_group(call.message, uid)
    await call.answer()


def _parse_mines_g(data):
    parts = data.split("|")
    mines = int(parts[0]) if parts[0] else 5
    mine_pos = set(map(int, parts[1].split(","))) if len(parts) > 1 and parts[1] else set()
    opened = set(map(int, parts[2].split(","))) if len(parts) > 2 and parts[2] else set()
    return mines, mine_pos, opened


def _mines_kb_g(opened, uid, mult, mine_pos=None, reveal=False):
    rows = []
    for r in range(5):
        row = []
        for c in range(5):
            i = r * 5 + c
            if reveal and mine_pos and i in mine_pos:
                row.append(InlineKeyboardButton(text="💣", callback_data=f"g:mnoop:{uid}"))
            elif i in opened:
                row.append(InlineKeyboardButton(text="💎", callback_data=f"g:mnoop:{uid}"))
            elif reveal:
                row.append(InlineKeyboardButton(text="⬜", callback_data=f"g:mnoop:{uid}"))
            else:
                row.append(InlineKeyboardButton(text="⬜", callback_data=f"g:mopen:{i}:{uid}"))
        rows.append(row)
    rows.append([InlineKeyboardButton(text=f"💰 Забрать {mult:.2f}x",
                                      callback_data=f"g:mcash:{uid}")])
    return rows


async def _render_mines_group(msg, uid):
    game = db.get_active_game(uid)
    if not game or game[0] != "mines":
        return
    _, _, bet, mult, data = game
    mines, mine_pos, opened = _parse_mines_g(data)

    rows = _mines_kb_g(opened, uid, mult)
    text = (f"💣 <b>Мины</b> ({mines} мин)\n"
            f"Открыто: <b>{len(opened)}</b> | Множитель: <b>{mult:.2f}x</b>\n"
            f"{BET} Ставка: <b>{bet}</b> {DOLLAR}")
    try:
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
                            parse_mode="HTML")
    except Exception:
        await msg.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
                         parse_mode="HTML")


@router.callback_query(F.data.startswith("g:mnoop:"))
async def g_mnoop(call: types.CallbackQuery):
    await call.answer()


@router.callback_query(F.data.startswith("g:mopen:"))
async def g_mopen(call: types.CallbackQuery):
    parts = call.data.split(":")
    idx = int(parts[2])
    uid = int(parts[3])
    if not _check_owner(call, uid):
        return await _not_owner(call)

    game = db.get_active_game(uid)
    if not game or game[0] != "mines":
        return await call.answer("❌ Игра не найдена", show_alert=True)

    _, _, bet, mult, data = game
    mines, mine_pos, opened = _parse_mines_g(data)
    if idx in opened:
        return await call.answer()

    if idx in mine_pos:
        db.add_loss(uid, bet)
        db.add_game(uid, "mines", bet, 0, 0, "lose")
        db.delete_active_game(uid)
        rows = _mines_kb_g(opened, uid, mult, mine_pos, reveal=True)
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

    await _render_mines_group(call.message, uid)
    await call.answer(f"💎 {new_mult:.2f}x")


@router.callback_query(F.data.startswith("g:mcash:"))
async def g_mcash(call: types.CallbackQuery):
    uid = int(call.data.split(":")[2])
    if not _check_owner(call, uid):
        return await _not_owner(call)

    game = db.get_active_game(uid)
    if not game or game[0] != "mines":
        return await call.answer("❌", show_alert=True)
    _, _, bet, mult, data = game
    mines, mine_pos, opened = _parse_mines_g(data)
    if not opened:
        return await call.answer("❌ Открой ячейку!", show_alert=True)

    win = round(bet * mult, 2)
    db.update_balance(uid, win)
    db.add_win(uid, win)
    db.add_game(uid, "mines", bet, win, mult, "win")
    db.delete_active_game(uid)

    await call.message.edit_text(
        f"💰 <b>Забрали!</b>\nМножитель: <b>{mult:.2f}x</b>\n"
        f"✅ +{win:.2f} {DOLLAR}\n"
        f"{WALLET} Баланс: <b>{db.get_balance(uid):.2f}</b>",
        parse_mode="HTML")
    await call.answer("✅")


# ============================================================
#              БАШНЯ
# ============================================================
async def _render_tower_group(msg, uid):
    game = db.get_active_game(uid)
    if not game or game[0] != "tower":
        return
    _, _, bet, mult, data = game
    level = int(data)
    rows = [[InlineKeyboardButton(text="⬆️ Подняться", callback_data=f"g:tup:{uid}")]]
    if level > 0:
        rows.append([InlineKeyboardButton(text=f"💰 Забрать {mult:.2f}x",
                                          callback_data=f"g:tcs:{uid}")])
    text = (f"🏰 <b>Башня</b>\nУровень: <b>{level}</b> | x{mult:.2f}\n"
            f"{BET} Ставка: <b>{bet}</b> {DOLLAR}")
    try:
        await msg.edit_text(text,
                            reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
                            parse_mode="HTML")
    except Exception:
        await msg.answer(text,
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
                         parse_mode="HTML")


@router.callback_query(F.data.startswith("g:tup:"))
async def g_tower_up(call: types.CallbackQuery):
    uid = int(call.data.split(":")[2])
    if not _check_owner(call, uid):
        return await _not_owner(call)
    game = db.get_active_game(uid)
    if not game or game[0] != "tower":
        return await call.answer("❌", show_alert=True)

    _, _, bet, mult, data = game
    level = int(data)
    if random.random() < 0.7:
        new_level = level + 1
        new_mult = tower_multiplier(new_level)
        db.set_active_game(uid, "tower", "playing", bet, new_mult, str(new_level))
        await _render_tower_group(call.message, uid)
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


@router.callback_query(F.data.startswith("g:tcs:"))
async def g_tower_cash(call: types.CallbackQuery):
    uid = int(call.data.split(":")[2])
    if not _check_owner(call, uid):
        return await _not_owner(call)
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
        f"💰 <b>Забрали!</b>\nУровень: {level} | x{mult:.2f}\n"
        f"✅ +{win:.2f} {DOLLAR}\n"
        f"{WALLET} Баланс: <b>{db.get_balance(uid):.2f}</b>",
        parse_mode="HTML")
    await call.answer("✅")


# ============================================================
#              КРАШ
# ============================================================
async def _crash_loop_group(uid, msg, crash_point, bet):
    mult = 1.0
    while mult < crash_point and mult < 50:
        await asyncio.sleep(0.7)
        mult = round(mult + 0.05, 2)
        game = db.get_active_game(uid)
        if not game or game[0] != "crash":
            return
        db.set_active_game(uid, "crash", "playing", bet, mult,
                           f"{crash_point}|{mult}")
        try:
            await msg.edit_text(
                f"🚀 <b>Краш</b>\nМножитель: <b>{mult:.2f}x</b>",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=f"💰 Забрать {mult:.2f}x",
                                          callback_data=f"g:ccs:{uid}")],
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
            f"💥 <b>КРАШ на {crash_point:.2f}x!</b>\n"
            f"Потеряно: <b>{bet}</b> {DOLLAR}\n"
            f"{WALLET} Баланс: <b>{db.get_balance(uid):.2f}</b>",
            parse_mode="HTML")
    except Exception:
        pass


@router.callback_query(F.data.startswith("g:ccs:"))
async def g_crash_cash(call: types.CallbackQuery):
    uid = int(call.data.split(":")[2])
    if not _check_owner(call, uid):
        return await _not_owner(call)
    game = db.get_active_game(uid)
    if not game or game[0] != "crash":
        return await call.answer("❌", show_alert=True)
    _, _, bet, mult, data = game
    parts = data.split("|")
    crash_point = float(parts[0])
    current = float(parts[1]) if len(parts) > 1 else 1.0
    if current >= crash_point:
        db.add_loss(uid, bet)
        db.add_game(uid, "crash", bet, 0, 0, "lose")
        db.delete_active_game(uid)
        return await call.answer("💥 Уже краш!", show_alert=True)
    win = round(bet * current, 2)
    db.update_balance(uid, win)
    db.add_win(uid, win)
    db.add_game(uid, "crash", bet, win, current, "win")
    db.delete_active_game(uid)
    await call.message.edit_text(
        f"💰 <b>Забрали на {current:.2f}x!</b>\n"
        f"✅ +{win:.2f} {DOLLAR}\n"
        f"{WALLET} Баланс: <b>{db.get_balance(uid):.2f}</b>",
        parse_mode="HTML")
    await call.answer("✅")


# ============================================================
#              ФИНИШ (для кубиков/спорта/слотов)
# ============================================================
async def _finish_group(call, uid, game_key, emoji, value,
                        bet, win, result, mult):
    uname = call.from_user.full_name or "Игрок"
    mention = f'<a href="tg://user?id={uid}">{uname}</a>'
    bet_int = db.get_bet(uid)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Повторить",
                              callback_data=f"g:repeat:{game_key}:{uid}"),
         InlineKeyboardButton(text="🎮 Меню игр",
                              callback_data=f"g:games_back:{uid}",
                              style="primary")],
    ])

    if result == "win":
        db.update_balance(uid, win)
        db.add_win(uid, win)
        db.add_game(uid, game_key, bet, win, mult, "win")
        await call.message.reply(
            f"🔼 {mention} выигрывает <b>{win - bet:.2f}</b> {DOLLAR}\n\n"
            f"<blockquote>{emoji} Выпало: <b>{value}</b>\n"
            f"{BET} Ставка: <b>{bet:.2f}</b> {DOLLAR}\n"
            f"{WALLET} Баланс: <b>{db.get_balance(uid):.2f}</b> {DOLLAR}</blockquote>",
            reply_markup=kb, parse_mode="HTML")
    else:
        db.add_loss(uid, bet)
        db.add_game(uid, game_key, bet, 0, 0, "lose")
        await call.message.reply(
            f"🔽 {mention} проигрывает <b>{bet:.2f}</b> {DOLLAR}\n\n"
            f"<blockquote>{emoji} Выпало: <b>{value}</b>\n"
            f"{BET} Ставка: <b>{bet:.2f}</b> {DOLLAR}\n"
            f"{WALLET} Баланс: <b>{db.get_balance(uid):.2f}</b> {DOLLAR}</blockquote>",
            reply_markup=kb, parse_mode="HTML")


# ============================================================
#              ПОВТОРИТЬ
# ============================================================
@router.callback_query(F.data.startswith("g:repeat:"))
async def g_repeat(call: types.CallbackQuery):
    parts = call.data.split(":")
    game = parts[2]
    uid = int(parts[3])
    if not _check_owner(call, uid):
        return await _not_owner(call)
    # Просто открываем меню игры
    fake_data = f"g:menu:{game}:{uid}"
    call.data = fake_data
    await group_menu_choice(call)