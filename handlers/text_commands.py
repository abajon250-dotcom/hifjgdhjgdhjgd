import re
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from keyboards.inline import (games_main, deposit_menu, withdraw_menu,
                              back_menu, mines_count_menu)
from utils.user_state import get_bet, set_bet
from utils.emoji import (DOLLAR, WALLET, BET, FLY_MONEY, DICE, PROFILE,
                          STATS, REF, TOP, VIP, GAMES, TIME)

router = Router()
ADMIN_ID = int(__import__("os").getenv("ADMIN_ID", 0))


def _amount(text):
    m = re.search(r"([\d.,]+)", text)
    if not m: return None
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
                              style="danger")]])
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
    text = (f"📊 <b>Статистика игрока</b>\n"
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
            f"{REF} <b>Рефералов:</b> {s['invited']}")
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
        f"• <code>баланс</code> / <code>профиль</code> / <code>топ</code>\n"
        f"• <code>меню</code> / <code>игры</code> / <code>wager</code>\n\n"
        f"💰 <b>Ставка:</b> <code>5$</code> или <code>ставка 5</code>\n"
        f"• <code>вб</code> — весь баланс\n"
        f"• <code>деп 5</code> / <code>вывод 5</code>\n"
        f"• <code>промо КОД</code>\n\n"
        f"🎲 <b>Кубики:</b>\n"
        f"• <code>куб 5</code> / <code>куб чет</code> / <code>куб нечет</code>\n"
        f"• <code>куб больше</code> / <code>куб меньше</code>\n"
        f"• <code>куб число 5</code> / <code>куб нет 6</code>\n"
        f"• <code>куб 7-</code> / <code>куб 7+</code> / <code>куб 7</code>\n\n"
        f"⚽ <b>Спорт (пара слов):</b>\n"
        f"• <code>футбол гол</code> / <code>футбол мимо</code> / <code>футбол штанга</code>\n"
        f"• <code>баскет гол</code> / <code>баскет отскок</code> / <code>баскет красный</code> / <code>баскет белый</code>\n"
        f"• <code>дартс центр</code> / <code>дартс промах</code> / <code>дартс штанга</code>\n"
        f"• <code>боулинг страйк</code> / <code>боулинг промах</code>\n\n"
        f"🎮 <b>Остальные:</b>\n"
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
                              style="danger")]])
    await message.answer(
        f"{WALLET} <b>Кошелёк</b>\n\n"
        f"{DOLLAR} Баланс: <b>{bal:.2f}</b>\n"
        f"{BET} Ставка: <b>{bet}</b>\n"
        f"{FLY_MONEY} Оборот: <b>{s['total_wagered']:.2f}</b>\n"
        f"{DICE} Игр: <b>{s['games_played']}</b>\n\n"
        f"Выберите действие:", reply_markup=kb, parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^(игры|играть|и|games|game)$"))
async def cmd_games(message: types.Message):
    uid = message.from_user.id
    bal = db.get_balance(uid)
    bet = db.get_bet(uid)
    await message.answer(
        f"{GAMES} <b>Выбирайте игру для ставки!</b>\n\n"
        f"{DOLLAR} Баланс — <b>{bal:.2f}</b>\n"
        f"{BET} Ставка — <b>{bet}</b>",
        reply_markup=games_main(uid), parse_mode="HTML")


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
            f"❌ <b>Ставка больше баланса</b>\n\n"
            f"{DOLLAR} Баланс: <b>{bal:.2f}</b>", parse_mode="HTML")
    if db.set_bet(uid, bet):
        await message.answer(f"✅ Ставка: <b>{bet}</b> {DOLLAR}",
                             reply_markup=back_menu(), parse_mode="HTML")


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


@router.message(F.text.regexp(r"^\s*\d+(?:[.,]\d+)?\s*\$\s*$"))
async def cmd_bet_short(message: types.Message):
    uid = message.from_user.id
    t = (message.text or "").strip().replace("$", "").replace(",", ".").strip()
    try:
        bet = float(t)
        if bet <= 0: return
    except Exception:
        return
    bal = db.get_balance(uid)
    if bet > bal:
        return await message.answer(
            f"❌ <b>Ставка больше баланса</b>\n\n"
            f"{DOLLAR} Баланс: <b>{bal:.2f}</b>", parse_mode="HTML")
    db.set_bet(uid, bet)


@router.message(F.text.regexp(r"(?i)^(деп|депозит|пополнить|пополнение)\s+([\d.,]+)$"))
async def cmd_dep_amount(message: types.Message, state: FSMContext):
    amount = _amount(message.text)
    if not amount or amount < 0.2:
        return await message.answer(f"❌ Минимум 0.2 {DOLLAR}", parse_mode="HTML")
    await state.update_data(dep_amount=amount)
    uid = message.from_user.id
    db.get_user(uid)
    bal = db.get_balance(uid)
    bet = db.get_bet(uid)
    await message.answer(
        f"💰 <b>Пополнение на {amount:.2f} {DOLLAR}</b>\n\n"
        f"{DOLLAR} Баланс — <b>{bal:.2f}</b>\n"
        f"{BET} Ставка — <b>{bet}</b>\n\n"
        f"<b>Выберите способ 👇</b>", reply_markup=deposit_menu(), parse_mode="HTML")


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
        f"<b>Выберите способ 👇</b>", reply_markup=deposit_menu(), parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^(вывод|вывести)\s+([\d.,]+)$"))
async def cmd_wd_amount(message: types.Message, state: FSMContext):
    amount = _amount(message.text)
    if not amount or amount < 0.4:
        return await message.answer(f"❌ Минимум для вывода: 0.4 {DOLLAR}",
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


@router.message(F.text.regexp(r"(?i)^промо\s+(\S+)$"))
async def cmd_promo(message: types.Message):
    m = re.search(r"промо\s+(\S+)", message.text, re.IGNORECASE)
    code = m.group(1).strip().upper()
    info = db.get_promo_info(code)
    if not info:
        return await message.answer("❌ <b>Промокод не найден</b>",
                                    reply_markup=back_menu(), parse_mode="HTML")
    if info["uses_left"] <= 0:
        return await message.answer("❌ <b>Промокод закончился</b>",
                                    reply_markup=back_menu(), parse_mode="HTML")
    wager_line = ""
    if info["required_wager"] > 0:
        wager_line = (f"📊 Требуется оборот: "
                      f"<b>{info['required_wager']:.2f}</b> USDT\n")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Активировать промокод",
                              callback_data=f"activate_promo:{code}",
                              style="success")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_main",
                              style="danger")]])
    await message.answer(
        f"🎁 <b>Промокод найден!</b>\n\n"
        f"💰 Сумма: <b>{info['amount']:.2f}</b> USDT\n"
        f"{wager_line}\n"
        f"Нажми кнопку ниже 👇", reply_markup=kb, parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^промо$"))
async def cmd_promo_hint(message: types.Message):
    await message.answer("🎁 Напиши: <code>промо КОД</code>",
                         reply_markup=back_menu(), parse_mode="HTML")


# ============================================================
#              КУБ ПО ТЕКСТУ
# ============================================================
@router.message(F.text.regexp(r"(?i)^куб\s+([1-6])$"))
async def go_dice_num(message: types.Message):
    from handlers.dice_games import play_dice_direct
    n = int(message.text.split()[-1])
    await play_dice_direct(message, 1, f"num{n}")


@router.message(F.text.regexp(r"(?i)^куб\s+(чет|чёт)$"))
async def go_dice_even(message: types.Message):
    from handlers.dice_games import play_dice_direct
    await play_dice_direct(message, 1, "even")


@router.message(F.text.regexp(r"(?i)^куб\s+(нечет|нечёт)$"))
async def go_dice_odd(message: types.Message):
    from handlers.dice_games import play_dice_direct
    await play_dice_direct(message, 1, "odd")


@router.message(F.text.regexp(r"(?i)^куб\s+(меньше|мень)$"))
async def go_dice_less_cmd(message: types.Message):
    from handlers.dice_games import play_dice_direct
    await play_dice_direct(message, 1, "less")


@router.message(F.text.regexp(r"(?i)^куб\s+(больше|бол)$"))
async def go_dice_more_cmd(message: types.Message):
    from handlers.dice_games import play_dice_direct
    await play_dice_direct(message, 1, "more")


@router.message(F.text.regexp(r"(?i)^куб\s+числ[оа]\s+([1-6])$"))
async def go_dice_num_word(message: types.Message):
    n = int(re.search(r"([1-6])", message.text).group(1))
    from handlers.dice_games import play_dice_direct
    await play_dice_direct(message, 1, f"num{n}")


@router.message(F.text.regexp(r"(?i)^куб\s+нет\s*([1-6])$|^куб\s+без\s*([1-6])$"))
async def go_dice_no_num(message: types.Message):
    n = int(re.search(r"([1-6])", message.text).group(1))
    from handlers.dice_games import play_dice_direct
    if n == 6:
        await play_dice_direct(message, 1, "no_6")
    else:
        await message.answer("❌ Пока доступно только <code>куб нет 6</code>",
                             parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^куб\s*7-$"))
async def go_dice_less7(message: types.Message):
    from handlers.dice_games import play_dice_direct
    await play_dice_direct(message, 2, "sum7_less")


@router.message(F.text.regexp(r"(?i)^куб\s*7\+$"))
async def go_dice_more7(message: types.Message):
    from handlers.dice_games import play_dice_direct
    await play_dice_direct(message, 2, "sum7_greater")


@router.message(F.text.regexp(r"(?i)^куб\s*7$"))
async def go_dice_sum7(message: types.Message):
    from handlers.dice_games import play_dice_direct
    await play_dice_direct(message, 2, "sum7_exact")


@router.message(F.text.regexp(r"(?i)^(слоты|слот)$"))
async def go_slots(message: types.Message):
    from handlers.slots import play_slots_direct
    await play_slots_direct(message, "any")


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


@router.message(F.text.regexp(r"(?i)^(футбол|баскет|дартс|боулинг)\s+\S+$"))
async def go_sport_text(message: types.Message):
    parts = (message.text or "").lower().split()
    if len(parts) != 2: return
    key = (parts[0], parts[1])
    if key not in SPORT_TEXT:
        opts = ", ".join(k[1] for k in SPORT_TEXT if k[0] == parts[0])
        return await message.answer(
            f"❌ Не знаю <code>{parts[1]}</code> для «{parts[0]}»\n"
            f"Доступно: <b>{opts}</b>", parse_mode="HTML")
    game, choice = SPORT_TEXT[key]
    from handlers.sport_games import play_sport_direct
    await play_sport_direct(message, game, choice)


@router.message(F.text.regexp(r"(?i)^(мины|мина)$"))
async def go_mines(message: types.Message):
    uid = message.from_user.id
    bet = get_bet(uid)
    await message.answer(
        f"💣 Ставка: <b>{bet}</b> {DOLLAR}\nВыберите кол-во мин:",
        reply_markup=mines_count_menu(uid), parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^(башня|tower)$"))
async def go_tower(message: types.Message):
    uid = message.from_user.id
    bet = get_bet(uid)
    if not db.has_enough(uid, bet):
        return await message.answer(f"❌ Нужно <b>{bet}</b> {DOLLAR}",
                                    parse_mode="HTML")
    db.update_balance(uid, -bet)
    db.add_wager(uid, bet)
    db.inc_games(uid)
    db.set_active_game(uid, "tower", "playing", bet, 1.0, "0")
    from handlers.arcades import _render_tower
    await _render_tower(message, uid)


@router.message(F.text.regexp(r"(?i)^(краш|crash)$"))
async def go_crash(message: types.Message):
    uid = message.from_user.id
    bet = get_bet(uid)
    if not db.has_enough(uid, bet):
        return await message.answer(f"❌ Нужно <b>{bet}</b> {DOLLAR}",
                                    parse_mode="HTML")
    from handlers.arcades import start_crash_direct
    await start_crash_direct(message, uid, bet)


@router.message(F.text.regexp(r"(?i)^(кено|keno)$"))
async def go_keno(message: types.Message):
    uid = message.from_user.id
    bet = get_bet(uid)
    if not db.has_enough(uid, bet):
        return await message.answer(f"❌ Нужно <b>{bet}</b> {DOLLAR}",
                                    parse_mode="HTML")
    from handlers.arcades import play_keno_direct
    await play_keno_direct(message, uid, bet)


@router.message(F.text.regexp(r"(?i)^(рулетка|руль)$"))
async def go_roulette(message: types.Message):
    uid = message.from_user.id
    bet = get_bet(uid)
    if not db.has_enough(uid, bet):
        return await message.answer(f"❌ Нужно <b>{bet}</b> {DOLLAR}",
                                    parse_mode="HTML")
    from handlers.arcades import play_roulette_direct
    await play_roulette_direct(message, uid, bet)


@router.callback_query(F.data.startswith("replay:"))
async def replay_game(call: types.CallbackQuery):
    parts = call.data.split(":")
    if len(parts) < 4: return await call.answer()
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
        await play_sport_direct(call.message, game_type.replace("sport_", ""),
                                choice, uid=uid)
    elif game_type == "slots":
        from handlers.slots import play_slots_direct
        await play_slots_direct(call.message, choice, uid=uid)
    await call.answer()