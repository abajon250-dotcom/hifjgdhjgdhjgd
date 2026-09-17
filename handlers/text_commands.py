import re
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from keyboards.inline import (games_main, deposit_menu, withdraw_menu,
                              back_menu)
from utils.user_state import get_bet, set_bet
from utils.emoji import (DOLLAR, WALLET, BET, FLY_MONEY, DICE, PROFILE,
                          STATS, REF, TOP, VIP, GAMES, TIME)

router = Router()
ADMIN_ID = int(__import__("os").getenv("ADMIN_ID", 0))


def _amount(text):
    m = re.search(r"([\d.,]+)", text)
    if not m:
        return None
    try:
        v = float(m.group(1).replace(",", "."))
        return v if v > 0 else None
    except Exception:
        return None


@router.message(F.text.regexp(r"(?i)^(топ|top)$"))
async def cmd_top(message: types.Message):
    top = db.get_top_wagered(10)
    text = f"{TOP} <b>Топ игроков:</b>\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, (uid, uname, wag) in enumerate(top, 1):
        medal = medals[i - 1] if i <= 3 else f"{i}."
        name = uname or f"id{uid}"
        text += (f"{medal} <a href='tg://user?id={uid}'>{name}</a> — "
                 f"<b>{wag:.2f}</b> {DOLLAR}\n")
    await message.answer(text, reply_markup=back_menu(), parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^(профиль|проф|profile)$"))
async def cmd_profile(message: types.Message):
    uid = message.from_user.id
    db.get_user(uid)
    s = db.get_stats(uid)
    vip = db.get_vip_info(uid)
    next_name = vip["next"][1] if vip["next"] else "MAX"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Ввести промокод",
                              callback_data="promo_enter", style="success")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats",
                              style="primary")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_main",
                              style="danger")],
    ])
    await message.answer(
        f"{PROFILE} <b>Профиль</b>\n\n"
        f"{DOLLAR} Баланс: <b>{s['balance']:.2f}</b>\n"
        f"{VIP} VIP: <b>{vip['progress']:.0f}%</b> "
        f"({vip['current'][1]} → {next_name})\n"
        f"{DICE} Игр: <b>{s['games_played']}</b>\n"
        f"{REF} Приглашено: <b>{s['invited_count']}</b>\n\n"
        f"<b>Промокод</b> — активируй бонус: <code>промо КОД</code>",
        reply_markup=kb, parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^(/wager|вагер|оборот|стата)$"))
async def cmd_wager(message: types.Message):
    uid = message.from_user.id
    s = db.get_full_stats(uid)
    profit = s["won"] - s["lost"]
    sign = "🟢" if profit >= 0 else "🔴"
    text = (
        f"📊 <b>Статистика игрока</b>\n"
        f"<i>{message.from_user.full_name}</i>\n\n"
        f"{DOLLAR} <b>Баланс:</b> {s['balance']:.2f}\n"
        f"{FLY_MONEY} <b>Оборот:</b> {s['wagered']:.2f}\n\n"
        f"📥 <b>Пополнено:</b> {s['deposited']:.2f}\n"
        f"📤 <b>Выведено:</b> {s['withdrawn']:.2f}\n\n"
        f"✅ <b>Выиграно:</b> {s['won']:.2f}\n"
        f"❌ <b>Проиграно:</b> {s['lost']:.2f}\n"
        f"{sign} <b>Профит:</b> {profit:+.2f}\n\n"
        f"{DICE} <b>Игр:</b> {s['games']}\n"
        f"{TIME} <b>Дней:</b> {s['days']}\n"
        f"{REF} <b>Рефералов:</b> {s['invited']}"
    )
    await message.answer(text, reply_markup=back_menu(), parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^/reserve$"))
async def cmd_reserve(message: types.Message):
    from utils.treasury import get_full_treasury
    from utils.emoji import CRYPTOBOT, XROCKET, STAR
    try:
        t = await get_full_treasury()
    except Exception as e:
        return await message.answer(f"❌ {e}")

    lines = ["💼 <b>Балансы казино</b>\n"]
    lines.append(f"{CRYPTOBOT} CryptoBot: <b>{t['crypto_total']:.2f}</b> USDT")
    lines.append(f"{XROCKET} xRocket: <b>{t['xrocket_total']:.2f}</b> USDT")
    lines.append(f"{STAR} Stars: <b>{t['stars_manual']:.2f}</b>")
    lines.append(f"🔥 Hot: <b>{t['hot_manual']:.2f}</b>")
    lines.append(f"❄️ Cold: <b>{t['cold_manual']:.2f}</b>")
    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^(помощь|хелп|help|h)$"))
async def cmd_help(message: types.Message):
    bet = get_bet(message.from_user.id)
    await message.answer(
        f"⚙️ <b>Помощь</b>\n\n"
        f"{BET} Текущая ставка: <b>{bet}</b> {DOLLAR}\n\n"
        f"📝 <b>Основные:</b>\n"
        f"• <code>баланс</code> — кошелёк\n"
        f"• <code>меню</code> — главное меню\n"
        f"• <code>игры</code> — меню игр\n"
        f"• <code>профиль</code> — профиль\n"
        f"• <code>топ</code> — топ игроков\n"
        f"• <code>wager</code> — статистика\n\n"
        f"💰 <b>Ставка и деньги:</b>\n"
        f"• <code>ставка 0.2</code> — установить\n"
        f"• <code>вб</code> — весь баланс\n"
        f"• <code>деп 5</code> / <code>вывод 5</code>\n"
        f"• <code>промо КОД</code>\n\n"
        f"🎲 <b>Игры:</b>\n"
        f"• <code>куб 5</code> / <code>куб 3,4</code> / <code>куб 7+</code>\n"
        f"• <code>футбол</code> / <code>баскет</code> / <code>дартс</code> / <code>боулинг</code>\n"
        f"• <code>слоты</code> / <code>мины</code> / <code>башня</code>\n"
        f"• <code>краш</code> / <code>кено</code> / <code>рулетка</code>",
        reply_markup=back_menu(), parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^(баланс|бал|б|balance|bal|кошелёк)$"))
async def cmd_balance(message: types.Message):
    uid = message.from_user.id
    db.get_user(uid)
    bal = db.get_balance(uid)
    bet = db.get_bet(uid)
    s = db.get_stats(uid)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пополнить", callback_data="deposit",
                              icon_custom_emoji_id="5445355530111437729",
                              style="success"),
         InlineKeyboardButton(text="Вывести", callback_data="withdraw",
                              icon_custom_emoji_id="5443127283898405358",
                              style="danger")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_main",
                              style="danger")],
    ])
    await message.answer(
        f"{WALLET} <b>Кошелёк</b>\n\n"
        f"{DOLLAR} Баланс: <b>{bal:.2f}</b>\n"
        f"{BET} Ставка: <b>{bet}</b>\n"
        f"{FLY_MONEY} Оборот: <b>{s['total_wagered']:.2f}</b>\n"
        f"{DICE} Игр: <b>{s['games_played']}</b>\n\n"
        f"Выберите действие:",
        reply_markup=kb, parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^(игры|играть|и|games|game)$"))
async def cmd_games(message: types.Message):
    uid = message.from_user.id
    bal = db.get_balance(uid)
    bet = db.get_bet(uid)
    await message.answer(
        f"{GAMES} <b>Выбирайте игру для ставки!</b>\n\n"
        f"{DOLLAR} Баланс — <b>{bal:.2f}</b>\n"
        f"{BET} Ставка — <b>{bet}</b>",
        reply_markup=games_main(), parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^ставка$"))
async def cmd_bet_show(message: types.Message):
    bet = get_bet(message.from_user.id)
    await message.answer(f"{BET} Текущая ставка: <b>{bet}</b> {DOLLAR}",
                         reply_markup=back_menu(), parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^ставка\s+([\d.,]+)$"))
async def cmd_bet_set(message: types.Message):
    uid = message.from_user.id
    bet = _amount(message.text)
    if not bet:
        return await message.answer("❌ Формат: <code>ставка 0.2</code>",
                                    parse_mode="HTML")
    bal = db.get_balance(uid)
    if bet > bal:
        return await message.answer(
            f"❌ <b>Ставка больше баланса!</b>\n\n"
            f"{DOLLAR} Баланс: <b>{bal:.2f}</b>\n"
            f"{BET} Попытка: <b>{bet:.2f}</b>",
            parse_mode="HTML")
    ok = db.set_bet(uid, bet)
    if ok:
        await message.answer(f"✅ Ставка: <b>{bet}</b> {DOLLAR}",
                             reply_markup=back_menu(), parse_mode="HTML")
    else:
        await message.answer("❌ Не удалось установить ставку", parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^(вб|всё|все|allin|all)$"))
async def cmd_allin(message: types.Message):
    uid = message.from_user.id
    db.get_user(uid)
    bal = db.get_balance(uid)
    if bal <= 0:
        return await message.answer("❌ На балансе пусто.",
                                    reply_markup=back_menu(), parse_mode="HTML")
    db.set_bet(uid, bal)
    await message.answer(f"💥 <b>ВБ установлен: {bal:.2f}</b> {DOLLAR}",
                         reply_markup=back_menu(), parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^(деп|депозит|пополнить|пополнение)\s+([\d.,]+)$"))
async def cmd_dep_amount(message: types.Message, state: FSMContext):
    amount = _amount(message.text)
    if not amount or amount < 0.5:
        return await message.answer(f"❌ Минимум 0.5 {DOLLAR}", parse_mode="HTML")
    await state.update_data(dep_amount=amount)
    uid = message.from_user.id
    db.get_user(uid)
    bal = db.get_balance(uid)
    bet = db.get_bet(uid)
    await message.answer(
        f"💰 <b>Пополнение на {amount:.2f} {DOLLAR}</b>\n\n"
        f"{DOLLAR} Баланс — <b>{bal:.2f}</b>\n"
        f"{BET} Ставка — <b>{bet}</b>\n\n"
        f"<b>Выберите способ 👇</b>",
        reply_markup=deposit_menu(), parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^(деп|депозит|пополнить|пополнение)$"))
async def cmd_dep_menu(message: types.Message):
    uid = message.from_user.id
    db.get_user(uid)
    bal = db.get_balance(uid)
    bet = db.get_bet(uid)
    await message.answer(
        f"💰 <b>Пополнение баланса</b>\n\n"
        f"{DOLLAR} Баланс — <b>{bal:.2f}</b>\n"
        f"{BET} Ставка — <b>{bet}</b>\n\n"
        f"<b>Выберите способ 👇</b>",
        reply_markup=deposit_menu(), parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^(вывод|вывести)\s+([\d.,]+)$"))
async def cmd_wd_amount(message: types.Message, state: FSMContext):
    amount = _amount(message.text)
    if not amount or amount < 2:
        return await message.answer(f"❌ Минимум для вывода: 2 {DOLLAR}",
                                    parse_mode="HTML")
    bal = db.get_balance(message.from_user.id)
    if amount > bal:
        return await message.answer(
            f"❌ Недостаточно. Баланс: {bal:.2f} {DOLLAR}", parse_mode="HTML")
    await state.update_data(wd_amount=amount)
    await message.answer(f"📥 Вывод <b>{amount} {DOLLAR}</b>\n\nВыберите способ:",
                         reply_markup=withdraw_menu(), parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^(вывод|вывести)$"))
async def cmd_wd_menu(message: types.Message):
    await message.answer("📥 Вывод. Выберите способ:",
                         reply_markup=withdraw_menu(), parse_mode="HTML")


# ============================================================
#              ПРОМОКОД (текстом) → показывает кнопку
# ============================================================
@router.message(F.text.regexp(r"(?i)^промо\s+(\S+)$"))
async def cmd_promo(message: types.Message):
    m = re.search(r"промо\s+(\S+)", message.text, re.IGNORECASE)
    code = m.group(1).strip().upper()
    uid = message.from_user.id

    info = db.get_promo_info(code)
    if not info:
        return await message.answer(
            "❌ <b>Промокод не найден</b>",
            reply_markup=back_menu(), parse_mode="HTML")
    if info["uses_left"] <= 0:
        return await message.answer(
            "❌ <b>Промокод закончился</b>",
            reply_markup=back_menu(), parse_mode="HTML")

    wager_line = ""
    if info["required_wager"] > 0:
        wager_line = (f"📊 Требуется оборот: "
                      f"<b>{info['required_wager']:.2f}</b> USDT\n")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎁 Активировать промокод",
            callback_data=f"activate_promo:{code}",
            style="success")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_main",
                              style="danger")],
    ])
    await message.answer(
        f"🎁 <b>Промокод найден!</b>\n\n"
        f"💰 Сумма: <b>{info['amount']:.2f}</b> USDT\n"
        f"{wager_line}\n"
        f"Нажми кнопку ниже 👇",
        reply_markup=kb, parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^промо$"))
async def cmd_promo_hint(message: types.Message):
    await message.answer("🎁 Напиши: <code>промо КОД</code>",
                         reply_markup=back_menu(), parse_mode="HTML")


# ============================================================
#              КУБИКИ
# ============================================================
@router.message(F.text.regexp(r"(?i)^(куб|кубик|дайс|dice)\s+([1-6])$"))
async def cmd_dice1(message: types.Message):
    uid = message.from_user.id
    num = int(message.text.split()[-1])
    bet = get_bet(uid)
    if not db.has_enough(uid, bet):
        return await message.answer(f"❌ Нужно <b>{bet}</b> {DOLLAR}", parse_mode="HTML")
    await message.answer(
        f"🎲 <a href='tg://user?id={uid}'>{message.from_user.full_name}</a>, "
        f"{BET} <b>{bet}</b> {DOLLAR} на число <b>{num}</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"Бросить на {num}",
                                  callback_data=f"d1:num{num}:{uid}", style="success")],
            [InlineKeyboardButton(text="Назад", callback_data="games_main",
                                  style="danger")],
        ]), parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^(куб|кубик|дайс|dice)\s+([1-6])\s*,\s*([1-6])$"))
async def cmd_dice1_two(message: types.Message):
    uid = message.from_user.id
    nums = re.findall(r"[1-6]", message.text)
    a, b = int(nums[0]), int(nums[1])
    if a == b:
        return await message.answer("❌ Числа разные")
    bet = get_bet(uid)
    if not db.has_enough(uid, bet):
        return await message.answer(f"❌ Нужно <b>{bet}</b> {DOLLAR}", parse_mode="HTML")
    await message.answer(
        f"🎲 <a href='tg://user?id={uid}'>{message.from_user.full_name}</a>, "
        f"{BET} <b>{bet}</b> {DOLLAR} на {a} и {b}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Бросить",
                                  callback_data=f"d1two:{a},{b}:{uid}", style="success")],
            [InlineKeyboardButton(text="Назад", callback_data="games_main",
                                  style="danger")],
        ]), parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^(куб|кубик|дайс|dice)\s*7-$"))
async def cmd_dice2_less7(message: types.Message):
    uid = message.from_user.id
    bet = get_bet(uid)
    await message.answer(
        f"🎲🎲 <a href='tg://user?id={uid}'>{message.from_user.full_name}</a>, "
        f"{BET} <b>{bet}</b> {DOLLAR} на <b>меньше 7</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Бросить", callback_data=f"d2:less:{uid}",
                                  style="success")],
            [InlineKeyboardButton(text="Назад", callback_data="games_main",
                                  style="danger")],
        ]), parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^(куб|кубик|дайс|dice)\s*7\+$"))
async def cmd_dice2_greater7(message: types.Message):
    uid = message.from_user.id
    bet = get_bet(uid)
    await message.answer(
        f"🎲🎲 <a href='tg://user?id={uid}'>{message.from_user.full_name}</a>, "
        f"{BET} <b>{bet}</b> {DOLLAR} на <b>больше 7</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Бросить", callback_data=f"d2:more:{uid}",
                                  style="success")],
            [InlineKeyboardButton(text="Назад", callback_data="games_main",
                                  style="danger")],
        ]), parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^(куб|кубик|дайс|dice)\s*7$"))
async def cmd_dice2_sum7(message: types.Message):
    uid = message.from_user.id
    bet = get_bet(uid)
    await message.answer(
        f"🎲🎲 <a href='tg://user?id={uid}'>{message.from_user.full_name}</a>, "
        f"{BET} <b>{bet}</b> {DOLLAR} на <b>равно 7</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Бросить", callback_data=f"d2:sum7:{uid}",
                                  style="success")],
            [InlineKeyboardButton(text="Назад", callback_data="games_main",
                                  style="danger")],
        ]), parse_mode="HTML")


# ============================================================
#              СПОРТ
# ============================================================
def _sport_kb(prefix, items, uid):
    rows, row = [], []
    for text, code in items:
        row.append(InlineKeyboardButton(text=text,
                                        callback_data=f"{prefix}:{code}:{uid}"))
        if len(row) == 2:
            rows.append(row); row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="Назад", callback_data="games_main",
                                      style="danger")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(F.text.regexp(r"(?i)^(футбол|фут|football)$"))
async def cmd_football(message: types.Message):
    uid = message.from_user.id
    bet = get_bet(uid)
    items = [("Мимо (x3)","mimo"),("Штанга (x4)","shtanga"),("Центр (x2)","center"),
             ("От штанги (x3.5)","from_shtanga"),("Угол (x1.8)","corner")]
    await message.answer(
        f"⚽ <a href='tg://user?id={uid}'>{message.from_user.full_name}</a>, "
        f"{BET} <b>{bet}</b> {DOLLAR}",
        reply_markup=_sport_kb("fc", items, uid), parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^(баскет|баск|basket)$"))
async def cmd_basket(message: types.Message):
    uid = message.from_user.id
    bet = get_bet(uid)
    items = [("Отскок (x3)","otskok"),("Близко (x4)","blizko"),
             ("Застрял (x5)","zastryal"),("С краем (x2)","edge"),
             ("Прямое (x1.5)","direct")]
    await message.answer(
        f"🏀 <a href='tg://user?id={uid}'>{message.from_user.full_name}</a>, "
        f"{BET} <b>{bet}</b> {DOLLAR}",
        reply_markup=_sport_kb("bc", items, uid), parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^(дартс|darts)$"))
async def cmd_darts(message: types.Message):
    uid = message.from_user.id
    bet = get_bet(uid)
    items = [("Промах (x3)","miss"),("В центр (x5)","bull"),("Сектор 3","s3"),
             ("Сектор 4","s4"),("Сектор 5","s5"),("Сектор 6","s6")]
    await message.answer(
        f"🎯 <a href='tg://user?id={uid}'>{message.from_user.full_name}</a>, "
        f"{BET} <b>{bet}</b> {DOLLAR}",
        reply_markup=_sport_kb("dc", items, uid), parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^(боулинг|bowling)$"))
async def cmd_bowling(message: types.Message):
    uid = message.from_user.id
    bet = get_bet(uid)
    items = [("Промах (x3.5)","miss"),("1/6 (x4)","p1"),("3/6 (x3)","p3"),
             ("4/6 (x2.5)","p4"),("5/6 (x2)","p5"),("Страйк (x1.5)","strike")]
    await message.answer(
        f"🎳 <a href='tg://user?id={uid}'>{message.from_user.full_name}</a>, "
        f"{BET} <b>{bet}</b> {DOLLAR}",
        reply_markup=_sport_kb("wc", items, uid), parse_mode="HTML")

# ============================================================
#              СТАВКА ЧИСЛОМ: 24 или 24$
# ============================================================
# ============================================================
#              СТАВКА ЧИСЛОМ ТОЛЬКО С $: 24$ или 0.5$
# ============================================================
@router.message(F.text.regexp(r"^\s*\d+(?:[.,]\d+)?\s*\$\s*$"))
async def cmd_bet_short(message: types.Message):
    uid = message.from_user.id
    t = (message.text or "").strip().replace("$", "").replace(",", ".").strip()
    try:
        bet = float(t)
        if bet <= 0:
            return
    except Exception:
        return
    bal = db.get_balance(uid)
    if bet > bal:
        return await message.answer(
            f"❌ <b>Ставка больше баланса</b>\n\n"
            f"{DOLLAR} Баланс: <b>{bal:.2f}</b>\n"
            f"{BET} Попытка: <b>{bet:.2f}</b>",
            parse_mode="HTML")
    if db.set_bet(uid, bet):
        await message.answer(f"✅ Ставка: <b>{bet}</b> {DOLLAR}",
                             parse_mode="HTML")


# ============================================================
#              КУБИКИ ПО ТЕКСТУ — ПРЯМОЙ ЗАПУСК
# ============================================================
@router.message(F.text.regexp(r"(?i)^куб\s+([1-6])$"))
async def go_dice_num(message: types.Message):
    from handlers.dice_games import play_dice_direct
    n = int(message.text.split()[-1])
    await play_dice_direct(message, 1, f"num{n}")


@router.message(F.text.regexp(r"(?i)^куб\s*7-$"))
async def go_dice_less(message: types.Message):
    from handlers.dice_games import play_dice_direct
    await play_dice_direct(message, 2, "less")


@router.message(F.text.regexp(r"(?i)^куб\s*7\+$"))
async def go_dice_more(message: types.Message):
    from handlers.dice_games import play_dice_direct
    await play_dice_direct(message, 2, "more")


@router.message(F.text.regexp(r"(?i)^куб\s*7$"))
async def go_dice_sum7(message: types.Message):
    from handlers.dice_games import play_dice_direct
    await play_dice_direct(message, 2, "sum7_exact")


# ============================================================
#              СЛОТЫ ПО ТЕКСТУ
# ============================================================
@router.message(F.text.regexp(r"(?i)^(слоты|слот)$"))
async def go_slots(message: types.Message):
    from handlers.slots import play_slots_direct
    await play_slots_direct(message, "any")


# ============================================================
#              СПОРТ ПО ТЕКСТУ: "баскет гол" и т.д.
# ============================================================
SPORT_TEXT = {
    ("футбол", "гол"):     ("football",   "clean"),
    ("футбол", "мимо"):    ("football",   "miss"),
    ("футбол", "штанга"):  ("football",   "stuck"),
    ("баскет", "гол"):     ("basketball", "center"),
    ("баскет", "отскок"):  ("basketball", "bounce"),
    ("баскет", "красный"): ("basketball", "red"),
    ("баскет", "белый"):   ("basketball", "white"),
    ("дартс", "центр"):    ("darts",      "center"),
    ("дартс", "промах"):   ("darts",      "miss"),
    ("дартс", "штанга"):   ("darts",      "bar"),
    ("боулинг", "страйк"): ("bowling",    "strike"),
    ("боулинг", "промах"): ("bowling",    "miss"),
}


@router.message(F.text.regexp(
    r"(?i)^(футбол|баскет|дартс|боулинг)\s+\S+$"))
async def go_sport_text(message: types.Message):
    parts = (message.text or "").lower().split()
    if len(parts) != 2:
        return
    key = (parts[0], parts[1])
    if key not in SPORT_TEXT:
        opts = ", ".join(k[1] for k in SPORT_TEXT if k[0] == parts[0])
        return await message.answer(
            f"❌ Не знаю исход <code>{parts[1]}</code> для «{parts[0]}»\n\n"
            f"Доступные: <b>{opts}</b>", parse_mode="HTML")
    game, choice = SPORT_TEXT[key]
    from handlers.sport_games import play_sport_direct
    await play_sport_direct(message, game, choice)


# ============================================================
#              КНОПКА "ПОВТОРИТЬ"
# ============================================================
@router.callback_query(F.data.startswith("replay:"))
async def replay_game(call: types.CallbackQuery):
    parts = call.data.split(":")
    if len(parts) < 4:
        return await call.answer()
    game_type = parts[1]
    choice = parts[2]
    try:
        uid = int(parts[3])
    except Exception:
        uid = call.from_user.id
    if call.from_user.id != uid:
        return await call.answer("❌ Это не твоя игра!", show_alert=True)

    if game_type.startswith("dice"):
        from handlers.dice_games import play_dice_direct
        try:
            dtype = int(game_type.replace("dice", ""))
        except Exception:
            dtype = 1
        await play_dice_direct(call.message, dtype, choice, uid=uid)
    elif game_type.startswith("sport_"):
        from handlers.sport_games import play_sport_direct
        await play_sport_direct(call.message,
                                game_type.replace("sport_", ""),
                                choice, uid=uid)
    elif game_type == "slots":
        from handlers.slots import play_slots_direct
        await play_slots_direct(call.message, choice, uid=uid)
    await call.answer()