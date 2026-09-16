import re
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.enums import ChatType
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from keyboards.inline import (games_main, deposit_menu, withdraw_menu,
                              mines_count_menu, back_menu)
from utils.user_state import get_bet, set_bet
from utils.emoji import (DOLLAR, WALLET, BET, FLY_MONEY, DICE, PROFILE,
                          STATS, REF, TOP, VIP, GAMES, TIME)

router = Router()
ADMIN_ID = int(__import__("os").getenv("ADMIN_ID", 0))

# ⚠️ Только для ЛС — в группах работают команды из handlers/group.py
PVT = F.chat.type == ChatType.PRIVATE


def _amount(text):
    m = re.search(r"([\d.,]+)", text)
    if not m:
        return None
    try:
        v = float(m.group(1).replace(",", "."))
        return v if v > 0 else None
    except Exception:
        return None


# ============================================================
#                       ТОП
# ============================================================
@router.message(F.text.regexp(r"(?i)^(топ|top)$"), PVT)
async def cmd_top(message: types.Message):
    top = db.get_top_wagered(10)
    text = f"{TOP} <b>Топ игроков:</b>\n\n"
    for i, (uid, uname, wag) in enumerate(top, 1):
        text += f"{i}. {uname or uid} — <b>{wag:.2f}</b> {DOLLAR}\n"
    await message.answer(text, reply_markup=back_menu(), parse_mode="HTML")


# ============================================================
#                       ПРОФИЛЬ
# ============================================================
@router.message(F.text.regexp(r"(?i)^(профиль|проф|profile)$"), PVT)
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
        reply_markup=kb, parse_mode="HTML"
    )


# ============================================================
#                       ПОМОЩЬ
# ============================================================
@router.message(F.text.regexp(r"(?i)^(помощь|хелп|help)$"), PVT)
async def cmd_help(message: types.Message):
    bet = get_bet(message.from_user.id)
    await message.answer(
        "⚙️ <b>Помощь</b>\n\n"
        f"🎯 Текущая ставка: <b>{bet}</b> {DOLLAR}\n\n"
        "📝 <b>Основные:</b>\n"
        "• <code>баланс</code> — кошелёк\n"
        "• <code>меню</code> — главное меню\n"
        "• <code>игры</code> — меню игр\n"
        "• <code>профиль</code> — мой профиль\n"
        "• <code>топ</code> — топ игроков\n\n"
        "💰 <b>Ставка и деньги:</b>\n"
        "• <code>ставка 0.2</code> — установить ставку\n"
        "• <code>вб</code> — поставить весь баланс\n"
        "• <code>деп 5</code> — пополнить 5 USDT\n"
        "• <code>вывод 5</code> — вывести 5 USDT\n"
        "• <code>промо КОД</code> — активировать промокод\n\n"
        "🎲 <b>Игры:</b>\n"
        "• <code>куб 5</code> / <code>куб 3,4</code> / <code>куб 7+</code> / "
        "<code>куб 7-</code> / <code>куб 7</code>\n"
        "• <code>футбол</code> / <code>баскет</code> / <code>дартс</code> / <code>боулинг</code>\n"
        "• <code>слоты</code> / <code>мины</code> / <code>башня</code>\n"
        "• <code>краш</code> / <code>кено</code> / <code>рулетка</code>",
        reply_markup=back_menu(), parse_mode="HTML"
    )


# ============================================================
#                       СТАВКА
# ============================================================
@router.message(F.text.regexp(r"(?i)^ставка$"), PVT)
async def cmd_bet_show(message: types.Message):
    bet = get_bet(message.from_user.id)
    await message.answer(
        f"🎯 Текущая ставка: <b>{bet}</b> {DOLLAR}",
        reply_markup=back_menu(), parse_mode="HTML"
    )


@router.message(F.text.regexp(r"(?i)^ставка\s+([\d.,]+)$"), PVT)
async def cmd_bet_set(message: types.Message):
    bet = _amount(message.text)
    if not bet:
        return await message.answer("❌ Формат: <code>ставка 0.2</code>",
                                    parse_mode="HTML")
    set_bet(message.from_user.id, bet)
    await message.answer(f"✅ Ставка: <b>{bet}</b> {DOLLAR}",
                         reply_markup=back_menu(), parse_mode="HTML")


# ============================================================
#              ВБ — ВЕСЬ БАЛАНС
# ============================================================
@router.message(F.text.regexp(r"(?i)^(вб|всё|все|allin|all)$"), PVT)
async def cmd_allin(message: types.Message):
    uid = message.from_user.id
    db.get_user(uid)
    bal = db.get_balance(uid)
    if bal <= 0:
        return await message.answer("❌ На балансе пусто.",
                                    reply_markup=back_menu(), parse_mode="HTML")
    set_bet(uid, bal)
    await message.answer(
        f"💥 <b>ВБ установлен: {bal:.2f}</b> {DOLLAR}\n"
        f"Теперь играй — ставка = весь баланс.",
        reply_markup=back_menu(), parse_mode="HTML"
    )


# ============================================================
#              ДЕП / ВЫВОД
# ============================================================
@router.message(F.text.regexp(r"(?i)^(деп|депозит|пополнить|пополнение)\s+([\d.,]+)$"), PVT)
async def cmd_dep_amount(message: types.Message, state: FSMContext):
    amount = _amount(message.text)
    if not amount or amount < 0.5:
        return await message.answer("❌ Минимум 0.5 USDT")
    await state.update_data(dep_amount=amount)
    await message.answer(
        f"📤 Пополнение на <b>{amount} USDT</b>\n\nВыберите способ:",
        reply_markup=deposit_menu(), parse_mode="HTML"
    )


@router.message(F.text.regexp(r"(?i)^(деп|депозит|пополнить|пополнение)$"), PVT)
async def cmd_dep_menu(message: types.Message):
    await message.answer("📤 Пополнение. Выберите способ:",
                         reply_markup=deposit_menu(), parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^(вывод|вывести)\s+([\d.,]+)$"), PVT)
async def cmd_wd_amount(message: types.Message, state: FSMContext):
    amount = _amount(message.text)
    if not amount or amount < 0.5:
        return await message.answer("❌ Минимум 0.5 USDT")
    bal = db.get_balance(message.from_user.id)
    if amount > bal:
        return await message.answer(f"❌ Недостаточно. Баланс: {bal:.2f}")
    await state.update_data(wd_amount=amount)
    await message.answer(
        f"📥 Вывод <b>{amount} USDT</b>\n\nВыберите способ:",
        reply_markup=withdraw_menu(), parse_mode="HTML"
    )


@router.message(F.text.regexp(r"(?i)^(вывод|вывести)$"), PVT)
async def cmd_wd_menu(message: types.Message):
    await message.answer("📥 Вывод. Выберите способ:",
                         reply_markup=withdraw_menu(), parse_mode="HTML")


# ============================================================
#              ПРОМОКОД
# ============================================================
@router.message(F.text.regexp(r"(?i)^промо\s+(\S+)$"), PVT)
async def cmd_promo(message: types.Message):
    m = re.search(r"промо\s+(\S+)", message.text, re.IGNORECASE)
    code = m.group(1).strip().upper()
    uid = message.from_user.id
    amount = db.use_promo(uid, code)
    if amount > 0:
        await message.answer(
            f"🎁 <b>Промокод активирован!</b>\n\n"
            f"{DOLLAR} Зачислено: <b>+{amount:.2f}</b>\n"
            f"{WALLET} Баланс: <b>{db.get_balance(uid):.2f}</b>",
            reply_markup=back_menu(), parse_mode="HTML"
        )
    else:
        await message.answer(
            "❌ <b>Промокод не найден или уже использован</b>",
            reply_markup=back_menu(), parse_mode="HTML"
        )


@router.message(F.text.regexp(r"(?i)^промо$"), PVT)
async def cmd_promo_hint(message: types.Message):
    await message.answer(
        "🎁 <b>Ввод промокода</b>\n\n"
        "Напиши: <code>промо КОД</code>\n"
        "Например: <code>промо ONYX2025</code>",
        reply_markup=back_menu(), parse_mode="HTML"
    )


# ============================================================
#                       КУБИКИ — 1 КУБ
# ============================================================
@router.message(F.text.regexp(r"(?i)^(куб|кубик|дайс|dice)\s+([1-6])$"), PVT)
async def cmd_dice1(message: types.Message):
    num = int(message.text.split()[-1])
    bet = get_bet(message.from_user.id)
    if not db.has_enough(message.from_user.id, bet):
        return await message.answer(
            f"❌ Нужно <b>{bet}</b> {DOLLAR}. Баланс: "
            f"<b>{db.get_balance(message.from_user.id):.2f}</b>",
            parse_mode="HTML"
        )
    await message.answer(
        f"🎲 Ставка: <b>{bet}</b> {DOLLAR} на число <b>{num}</b> (x6)",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"Бросить на {num}",
                                  callback_data=f"d1:num{num}", style="success")],
            [InlineKeyboardButton(text="Назад", callback_data="games_main",
                                  style="danger")],
        ]), parse_mode="HTML"
    )


@router.message(F.text.regexp(r"(?i)^(куб|кубик|дайс|dice)\s+([1-6])\s*,\s*([1-6])$"), PVT)
async def cmd_dice1_two(message: types.Message):
    nums = re.findall(r"[1-6]", message.text)
    if len(nums) < 2:
        return await message.answer("❌ Формат: <code>куб 3,4</code>", parse_mode="HTML")
    a, b = int(nums[0]), int(nums[1])
    if a == b:
        return await message.answer("❌ Числа должны быть разными", parse_mode="HTML")
    bet = get_bet(message.from_user.id)
    if not db.has_enough(message.from_user.id, bet):
        return await message.answer(f"❌ Нужно <b>{bet}</b> {DOLLAR}", parse_mode="HTML")
    await message.answer(
        f"🎲 Ставка: <b>{bet}</b> {DOLLAR} на числа <b>{a}</b> и <b>{b}</b> (x2.8)",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"Бросить на {a},{b}",
                                  callback_data=f"d1two:{a},{b}", style="success")],
            [InlineKeyboardButton(text="Назад", callback_data="games_main",
                                  style="danger")],
        ]), parse_mode="HTML"
    )


@router.message(F.text.regexp(r"(?i)^(куб|кубик|дайс|dice)\s*7-$"), PVT)
async def cmd_dice2_less7(message: types.Message):
    bet = get_bet(message.from_user.id)
    if not db.has_enough(message.from_user.id, bet):
        return await message.answer(f"❌ Нужно <b>{bet}</b> {DOLLAR}", parse_mode="HTML")
    await message.answer(
        f"🎲🎲 Ставка: <b>{bet}</b> {DOLLAR} на сумму <b>меньше 7</b> (x2)",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Бросить", callback_data="d2:less", style="success")],
            [InlineKeyboardButton(text="Назад", callback_data="games_main",
                                  style="danger")],
        ]), parse_mode="HTML"
    )


@router.message(F.text.regexp(r"(?i)^(куб|кубик|дайс|dice)\s*7\+$"), PVT)
async def cmd_dice2_greater7(message: types.Message):
    bet = get_bet(message.from_user.id)
    if not db.has_enough(message.from_user.id, bet):
        return await message.answer(f"❌ Нужно <b>{bet}</b> {DOLLAR}", parse_mode="HTML")
    await message.answer(
        f"🎲🎲 Ставка: <b>{bet}</b> {DOLLAR} на сумму <b>больше 7</b> (x2)",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Бросить", callback_data="d2:more", style="success")],
            [InlineKeyboardButton(text="Назад", callback_data="games_main",
                                  style="danger")],
        ]), parse_mode="HTML"
    )


@router.message(F.text.regexp(r"(?i)^(куб|кубик|дайс|dice)\s*7$"), PVT)
async def cmd_dice2_sum7(message: types.Message):
    bet = get_bet(message.from_user.id)
    if not db.has_enough(message.from_user.id, bet):
        return await message.answer(f"❌ Нужно <b>{bet}</b> {DOLLAR}", parse_mode="HTML")
    await message.answer(
        f"🎲🎲 Ставка: <b>{bet}</b> {DOLLAR} на сумму <b>равно 7</b> (x6)",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Бросить", callback_data="d2:sum7", style="success")],
            [InlineKeyboardButton(text="Назад", callback_data="games_main",
                                  style="danger")],
        ]), parse_mode="HTML"
    )


# ============================================================
#                       СПОРТ
# ============================================================
def _sport_kb(prefix, items):
    rows, row = [], []
    for text, code in items:
        row.append(InlineKeyboardButton(text=text, callback_data=f"{prefix}:{code}"))
        if len(row) == 2:
            rows.append(row); row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="Назад", callback_data="games_main",
                                      style="danger")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(F.text.regexp(r"(?i)^(футбол|фут|football)$"), PVT)
async def cmd_football(message: types.Message):
    bet = get_bet(message.from_user.id)
    items = [("Мимо (x3)","mimo"),("Штанга (x4)","shtanga"),("Центр (x2)","center"),
             ("От штанги (x3.5)","from_shtanga"),("Угол (x1.8)","corner")]
    await message.answer(f"⚽ Ставка: <b>{bet}</b> {DOLLAR}",
                         reply_markup=_sport_kb("fc", items), parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^(баскет|баск|basket)$"), PVT)
async def cmd_basket(message: types.Message):
    bet = get_bet(message.from_user.id)
    items = [("Отскок (x3)","otskok"),("Близко (x4)","blizko"),("Застрял (x5)","zastryal"),
             ("С краем (x2)","edge"),("Прямое (x1.5)","direct")]
    await message.answer(f"🏀 Ставка: <b>{bet}</b> {DOLLAR}",
                         reply_markup=_sport_kb("bc", items), parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^(дартс|darts)$"), PVT)
async def cmd_darts(message: types.Message):
    bet = get_bet(message.from_user.id)
    items = [("Промах (x3)","miss"),("В центр (x5)","bull"),("Сектор 3","s3"),
             ("Сектор 4","s4"),("Сектор 5","s5"),("Сектор 6","s6")]
    await message.answer(f"🎯 Ставка: <b>{bet}</b> {DOLLAR}",
                         reply_markup=_sport_kb("dc", items), parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^(боулинг|bowling)$"), PVT)
async def cmd_bowling(message: types.Message):
    bet = get_bet(message.from_user.id)
    items = [("Промах (x3.5)","miss"),("1/6 (x4)","p1"),("3/6 (x3)","p3"),
             ("4/6 (x2.5)","p4"),("5/6 (x2)","p5"),("Страйк (x1.5)","strike")]
    await message.answer(f"🎳 Ставка: <b>{bet}</b> {DOLLAR}",
                         reply_markup=_sport_kb("wc", items), parse_mode="HTML")


# ============================================================
#                       СЛОТЫ / АРКАДЫ
# ============================================================
@router.message(F.text.regexp(r"(?i)^(слоты|слот|slots)$"), PVT)
async def cmd_slots(message: types.Message):
    bet = get_bet(message.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="777 (x60)", callback_data="sl:777"),
         InlineKeyboardButton(text="77* (x15)", callback_data="sl:77x")],
        [InlineKeyboardButton(text="Любая комбинация (x15)", callback_data="sl:any")],
        [InlineKeyboardButton(text="Лаки 7 (до x370)", callback_data="sl:lucky7"),
         InlineKeyboardButton(text="Линии (до x150)", callback_data="sl:lines")],
        [InlineKeyboardButton(text="Сумма (до x6)", callback_data="sl:sum"),
         InlineKeyboardButton(text="Копилка (до x2.4)", callback_data="sl:piggy")],
        [InlineKeyboardButton(text="Лесенка (до x27)", callback_data="sl:ladder")],
        [InlineKeyboardButton(text="Назад", callback_data="games_main",
                              style="danger")],
    ])
    await message.answer(f"🎰 Ставка: <b>{bet}</b> {DOLLAR}",
                         reply_markup=kb, parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^(мины|mines)$"), PVT)
async def cmd_mines(message: types.Message):
    bet = get_bet(message.from_user.id)
    await message.answer(f"💣 Ставка: <b>{bet}</b> {DOLLAR}\nВыберите кол-во мин:",
                         reply_markup=mines_count_menu(), parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^(башня|tower)$"), PVT)
async def cmd_tower(message: types.Message):
    bet = get_bet(message.from_user.id)
    await message.answer(f"🏰 Ставка: <b>{bet}</b> {DOLLAR}",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                             [InlineKeyboardButton(text="Играть", callback_data="ar:tower",
                                                   style="success")],
                             [InlineKeyboardButton(text="Назад", callback_data="games_main",
                                                   style="danger")],
                         ]), parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^(краш|crash)$"), PVT)
async def cmd_crash(message: types.Message):
    bet = get_bet(message.from_user.id)
    await message.answer(f"🚀 Ставка: <b>{bet}</b> {DOLLAR}",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                             [InlineKeyboardButton(text="Играть", callback_data="ar:crash",
                                                   style="success")],
                             [InlineKeyboardButton(text="Назад", callback_data="games_main",
                                                   style="danger")],
                         ]), parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^(кено|keno)$"), PVT)
async def cmd_keno(message: types.Message):
    bet = get_bet(message.from_user.id)
    await message.answer(f"🎯 Ставка: <b>{bet}</b> {DOLLAR}",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                             [InlineKeyboardButton(text="Играть", callback_data="ar:keno",
                                                   style="success")],
                             [InlineKeyboardButton(text="Назад", callback_data="games_main",
                                                   style="danger")],
                         ]), parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^(рулетка|руль|roulette)$"), PVT)
async def cmd_roulette(message: types.Message):
    bet = get_bet(message.from_user.id)
    await message.answer(f"🎡 Ставка: <b>{bet}</b> {DOLLAR}",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                             [InlineKeyboardButton(text="Играть", callback_data="ar:roulette",
                                                   style="success")],
                             [InlineKeyboardButton(text="Назад", callback_data="games_main",
                                                   style="danger")],
                         ]), parse_mode="HTML")