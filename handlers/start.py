import os
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.enums import ChatType
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from keyboards.inline import (main_menu_inline, games_main, balance_menu,
                              referrals_menu, back_menu)
from keyboards.reply import main_menu
from utils.subscription import check_subscription, subscribe_kb, subscribe_text
from utils.safe_edit import safe_answer, safe_edit
from utils.emoji import (PROFILE, DOLLAR, FLY_MONEY, DICE, STATS, TIME,
                          VIP, BET, REF, LINK, GAMES, WALLET, TOP,
                          FOOTBALL, BASKET, DARTS, BOWLING, SLOTS,
                          WIN_LOSS, LOSE_LOSS)

router = Router()
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
CASINO_NAME = os.getenv("CASINO_NAME", "Onyx")
PVT = F.chat.type == ChatType.PRIVATE


def _main_text(uid, full_name):
    db.get_user(uid)
    s = db.get_stats(uid)
    vip = db.get_vip_info(uid)
    next_name = vip["next"][1] if vip["next"] else "MAX"
    next_emoji = vip["next"][2] if vip["next"] else "👑"
    return (
        f"{PROFILE} <b>#{uid} {full_name}</b>\n\n"
        f"{DOLLAR} <b>Баланс — {s['balance']:.2f}</b>\n\n"
        f"{VIP} <b>VIP — {vip['progress']:.0f}%</b>\n"
        f"{vip['current'][2]} {vip['current'][1]} → {next_emoji} {next_name}\n\n"
        f"{FLY_MONEY} Оборот: <b>{s['total_wagered']:.2f}</b>\n"
        f"{DICE} Игр: <b>{s['games_played']}</b>\n"
        f"{TIME} Дней: <b>{s['days_registered']}</b>"
    )


def _wallet_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пополнить", callback_data="deposit",
                              icon_custom_emoji_id="5445355530111437729",
                              style="success"),
         InlineKeyboardButton(text="Вывести", callback_data="withdraw",
                              icon_custom_emoji_id="5443127283898405358",
                              style="danger")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_main",
                              style="danger")],
    ])


def _wallet_text(uid):
    db.get_user(uid)
    bal = db.get_balance(uid)
    bet = db.get_bet(uid)
    s = db.get_stats(uid)
    return (
        f"{WALLET} <b>Кошелёк</b>\n\n"
        f"{DOLLAR} Баланс: <b>{bal:.2f}</b>\n"
        f"{BET} Ставка: <b>{bet}</b>\n"
        f"{FLY_MONEY} Оборот: <b>{s['total_wagered']:.2f}</b>\n"
        f"{DICE} Игр: <b>{s['games_played']}</b>\n\n"
        f"Выберите действие:"
    )


# ============================================================
#              /start — реф + промокод через ссылку
# ============================================================
@router.message(Command("start"), PVT)
async def cmd_start(message: types.Message):
    uid = message.from_user.id
    if db.is_banned(uid):
        return await message.answer("🚫 Вы забанены.")

    # Парсим payload ДО подписки
    args = message.text.split()
    if len(args) > 1:
        payload = args[1]
        print(f"[start] uid={uid} payload={payload}")

        # ---------- РЕФЕРАЛКА ----------
        if payload.startswith("ref"):
            try:
                ref_id = int(payload.replace("ref", ""))
                ok = db.set_referrer(uid, ref_id)
                if ok:
                    await message.answer(
                        "🤝 <b>Вы пришли по реферальной ссылке!</b>",
                        parse_mode="HTML")
            except Exception as e:
                print(f"[start] ref error: {e}")

        # ---------- ПРОМОКОД ----------
        elif payload.startswith("promo_") or payload.startswith("p_"):
            code = payload.split("_", 1)[1].strip().upper()
            info = db.get_promo_info(code)

            if not info:
                await message.answer(
                    f"❌ Промокод <code>{code}</code> не найден.",
                    parse_mode="HTML")
            elif info["uses_left"] <= 0:
                await message.answer(
                    f"❌ Промокод <code>{code}</code> закончился.",
                    parse_mode="HTML")
            else:
                wager_line = ""
                if info["required_wager"] > 0:
                    wager_line = (f"📊 Требуется оборот: "
                                  f"<b>{info['required_wager']:.2f}</b> USDT\n")
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="🎁 Активировать промокод",
                        callback_data=f"activate_promo:{code}",
                        style="success")],
                ])
                await message.answer(
                    f"🎁 <b>Промокод найден!</b>\n\n"
                    f"💰 Сумма: <b>{info['amount']:.2f}</b> USDT\n"
                    f"{wager_line}\n"
                    f"<b>Условия:</b>\n"
                    f"• Подписка на все каналы\n"
                    + (f"• Оборот от <b>{info['required_wager']:.0f}</b> USDT\n"
                       if info["required_wager"] > 0 else "")
                    + f"\nНажми кнопку ниже 👇",
                    reply_markup=kb, parse_mode="HTML")

    # Проверка подписки
    not_sub = await check_subscription(message.bot, uid)
    if not_sub and uid != ADMIN_ID:
        return await message.answer(subscribe_text(),
                                    reply_markup=subscribe_kb(),
                                    parse_mode="HTML")

    db.get_user(uid)
    db.set_username(uid, message.from_user.username or message.from_user.full_name)
    is_admin = (uid == ADMIN_ID)

    await message.answer(f"🎰 <b>{CASINO_NAME}</b>",
                         reply_markup=main_menu(is_admin), parse_mode="HTML")
    await safe_answer(message, _main_text(uid, message.from_user.full_name),
                      reply_markup=main_menu_inline(is_admin),
                      parse_mode="HTML")


# ============================================================
#              АКТИВАЦИЯ ПРОМОКОДА (кнопка)
# ============================================================
@router.callback_query(F.data.startswith("activate_promo:"))
async def activate_promo(call: types.CallbackQuery):
    code = call.data.split(":", 1)[1].upper()
    uid = call.from_user.id

    # 1) Проверка подписки
    not_sub = await check_subscription(call.bot, uid)
    if not_sub and uid != ADMIN_ID:
        await call.answer("🔒 Сначала подпишись на каналы!", show_alert=True)
        return await call.message.answer(
            subscribe_text(),
            reply_markup=subscribe_kb(),
            parse_mode="HTML")

    # 2) Проверка промокода
    info = db.get_promo_info(code)
    if not info:
        return await call.answer("❌ Промокод не найден.", show_alert=True)
    if info["uses_left"] <= 0:
        return await call.answer("❌ Промокод закончился.", show_alert=True)

    # 3) Проверка оборота
    s = db.get_stats(uid)
    if s["total_wagered"] < info["required_wager"]:
        need = info["required_wager"] - s["total_wagered"]
        return await call.answer(
            f"📊 Нужен оборот {info['required_wager']:.2f} USDT\n"
            f"У тебя: {s['total_wagered']:.2f}\n"
            f"Осталось: {need:.2f}",
            show_alert=True)

    # 4) Активация
    amount = db.use_promo(uid, code)
    if amount > 0:
        await call.message.edit_text(
            f"🎁 <b>Промокод активирован!</b>\n\n"
            f"💰 Зачислено: <b>+{amount:.2f}</b> USDT\n"
            f"💼 Баланс: <b>{db.get_balance(uid):.2f}</b> USDT",
            parse_mode="HTML")
        await call.answer("✅ Промокод активирован!")
    else:
        await call.answer("❌ Не удалось активировать (уже использован).",
                          show_alert=True)


@router.callback_query(F.data == "check_sub")
async def check_sub_cb(call: types.CallbackQuery):
    not_sub = await check_subscription(call.bot, call.from_user.id)
    if not_sub:
        return await call.answer("❌ Вы ещё не подписались!", show_alert=True)
    is_admin = (call.from_user.id == ADMIN_ID)
    await safe_edit(call.message,
                    _main_text(call.from_user.id, call.from_user.full_name),
                    reply_markup=main_menu_inline(is_admin),
                    parse_mode="HTML")
    await call.answer("✅ Спасибо за подписку!")


# ============================================================
#              REPLY-КНОПКИ
# ============================================================
@router.message(F.text.in_({"Баланс", "💰 Баланс", "Кошелёк", "💼 Кошелёк"}), PVT)
async def btn_wallet(message: types.Message):
    await safe_answer(message, _wallet_text(message.from_user.id),
                      reply_markup=_wallet_kb(), parse_mode="HTML")


@router.message(F.text.in_({"Играть", "🎮 Играть", "🎮"}), PVT)
async def btn_play(message: types.Message):
    uid = message.from_user.id
    bal = db.get_balance(uid)
    bet = db.get_bet(uid)
    await safe_answer(message,
        f"{GAMES} <b>Выбирайте игру для ставки!</b>\n\n"
        f"{DOLLAR} Баланс — <b>{bal:.2f}</b>\n"
        f"{BET} Ставка — <b>{bet}</b>",
        reply_markup=games_main(), parse_mode="HTML")


@router.message(F.text.in_({"Меню", "📋 Меню"}), PVT)
async def btn_menu(message: types.Message):
    uid = message.from_user.id
    if db.is_banned(uid):
        return
    not_sub = await check_subscription(message.bot, uid)
    if not_sub and uid != ADMIN_ID:
        return await message.answer(subscribe_text(),
                                    reply_markup=subscribe_kb(),
                                    parse_mode="HTML")
    db.get_user(uid)
    is_admin = (uid == ADMIN_ID)
    await safe_answer(message, _main_text(uid, message.from_user.full_name),
                      reply_markup=main_menu_inline(is_admin),
                      parse_mode="HTML")


# ============================================================
#              INLINE CALLBACKS
# ============================================================
@router.callback_query(F.data == "back_to_main")
async def back_to_main(call: types.CallbackQuery):
    uid = call.from_user.id
    is_admin = (uid == ADMIN_ID)
    await safe_edit(call.message, _main_text(uid, call.from_user.full_name),
                    reply_markup=main_menu_inline(is_admin), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "menu")
async def menu_cb(call: types.CallbackQuery):
    uid = call.from_user.id
    if db.is_banned(uid):
        return await call.answer("🚫 Забанен", show_alert=True)
    not_sub = await check_subscription(call.bot, uid)
    if not_sub and uid != ADMIN_ID:
        return await call.answer("🔒 Подпишись на каналы!", show_alert=True)
    is_admin = (uid == ADMIN_ID)
    await safe_edit(call.message, _main_text(uid, call.from_user.full_name),
                    reply_markup=main_menu_inline(is_admin), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "wallet")
async def wallet_cb(call: types.CallbackQuery):
    await safe_edit(call.message, _wallet_text(call.from_user.id),
                    reply_markup=_wallet_kb(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "profile")
async def profile_cb(call: types.CallbackQuery):
    uid = call.from_user.id
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
    await safe_edit(call.message,
        f"{PROFILE} <b>Профиль</b>\n\n"
        f"{DOLLAR} Баланс: <b>{s['balance']:.2f}</b>\n"
        f"{VIP} VIP: <b>{vip['progress']:.0f}%</b> "
        f"({vip['current'][1]} → {next_name})\n"
        f"{DICE} Игр: <b>{s['games_played']}</b>\n"
        f"{REF} Приглашено: <b>{s['invited_count']}</b>\n\n"
        f"<b>Промокод</b> — активируй бонус: <code>промо КОД</code>",
        reply_markup=kb, parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "promo_enter")
async def promo_enter(call: types.CallbackQuery):
    await call.message.answer(
        "🎁 <b>Введите промокод</b>\n\n"
        "Напиши в чат: <code>промо КОД</code>",
        reply_markup=back_menu(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "games_main")
async def games_main_handler(call: types.CallbackQuery):
    uid = call.from_user.id
    bal = db.get_balance(uid)
    bet = db.get_bet(uid)
    await safe_edit(call.message,
        f"{GAMES} <b>Выбирайте игру для ставки!</b>\n\n"
        f"{DOLLAR} Баланс — <b>{bal:.2f}</b>\n"
        f"{BET} Ставка — <b>{bet}</b>",
        reply_markup=games_main(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "stats")
async def stats_handler(call: types.CallbackQuery):
    s = db.get_stats(call.from_user.id)
    text = (
        f"{STATS} <b>Статистика</b>\n\n"
        f"{DOLLAR} Баланс: <b>{s['balance']:.2f}</b>\n"
        f"{FLY_MONEY} Оборот: <b>{s['total_wagered']:.2f}</b>\n"
        f"✅ Выиграно: <b>{s['total_won']:.2f}</b>\n"
        f"❌ Проиграно: <b>{s['total_lost']:.2f}</b>\n"
        f"📥 Пополнено: <b>{s['total_deposited']:.2f}</b>\n"
        f"📤 Выведено: <b>{s['total_withdrawn']:.2f}</b>\n"
        f"{DICE} Игр: <b>{s['games_played']}</b>\n"
        f"{REF} Приглашено: <b>{s['invited_count']}</b>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="По играм", callback_data="stats_games",
                              icon_custom_emoji_id="5321230889357713132",
                              style="primary")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_main",
                              style="danger")],
    ])
    await safe_edit(call.message, text, reply_markup=kb, parse_mode="HTML")
    await call.answer()


GAME_LABELS = {
    "dice_1": ("1 Куб", DICE), "dice_2": ("2 Куба", DICE), "dice_3": ("3 Куба", DICE),
    "sport_football": ("Футбол", FOOTBALL), "sport_basketball": ("Баскет", BASKET),
    "sport_darts": ("Дартс", DARTS), "sport_bowling": ("Боулинг", BOWLING),
    "slots": ("Слоты", SLOTS), "mines": ("Мины", "💣"), "tower": ("Башня", "🏰"),
    "crash": ("Краш", "🚀"), "keno": ("Кено", "🎯"), "roulette": ("Рулетка", "🎡"),
}


def _game_label(gtype):
    if gtype in GAME_LABELS:
        name, emoji = GAME_LABELS[gtype]
        return emoji, name
    if gtype.startswith("dice_"): return DICE, "Кубики"
    if gtype.startswith("sport_"): return DARTS, "Спорт"
    return GAMES, gtype


@router.callback_query(F.data == "stats_games")
async def stats_games(call: types.CallbackQuery):
    stats = db.get_games_stats(call.from_user.id)
    if not stats:
        return await call.answer("❌ Вы ещё не играли!", show_alert=True)
    text = "🎮 <b>Статистика по играм</b>\n\n"
    total = 0
    for gtype, s in sorted(stats.items(), key=lambda x: -x[1]["games"]):
        emoji, name = _game_label(gtype)
        profit = s["profit"]; total += profit
        sign = "🟢" if profit >= 0 else "🔴"
        text += (f"{emoji} <b>{name}</b>\n"
                 f"  🎯 Игр: <b>{s['games']}</b>  |  🔼 {s['wins']}  |  🔽 {s['losses']}\n"
                 f"  💵 Выиграно: <b>+{s['won']:.2f}</b>  |  💸 Поставлено: <b>-{s['staked']:.2f}</b>\n"
                 f"  {sign} Итог: <b>{'+' if profit >= 0 else ''}{profit:.2f}</b>\n\n")
    sign = "🟢" if total >= 0 else "🔴"
    text += f"━━━━━━━━━━━━━━━━━━\n{sign} <b>Общий: {'+' if total >= 0 else ''}{total:.2f}</b>"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="stats", style="danger")],
    ])
    await safe_edit(call.message, text, reply_markup=kb, parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "privacy")
async def privacy_handler(call: types.CallbackQuery):
    p = db.is_private(call.from_user.id)
    db.set_privacy(call.from_user.id, not p)
    await call.answer(f"Приватность: {'🔒 Скрыт' if not p else '👁 Открыт'}",
                      show_alert=True)


@router.callback_query(F.data == "bonuses")
async def bonuses_handler(call: types.CallbackQuery):
    uid = call.from_user.id
    if db.can_take_bonus(uid):
        db.take_bonus(uid, 1.0)
        await call.answer("🎁 Бонус 1.0 USDT получен!", show_alert=True)
    else:
        await call.answer("⏳ Раз в 24 часа.", show_alert=True)


@router.callback_query(F.data == "referrals")
async def referrals_handler(call: types.CallbackQuery):
    uid = call.from_user.id
    invited = db.get_stats(uid)["invited_count"]
    earned = db.get_ref_balance(uid)
    bot_info = await call.bot.get_me()
    link = f"https://t.me/{bot_info.username}?start=ref{uid}"
    text = (
        f"{REF} <b>Реферальная программа</b>\n\n"
        f"{LINK} <code>{link}</code>\n\n"
        f"👤 Приглашено: <b>{invited}</b>\n"
        f"{DOLLAR} Заработано: <b>{earned:.2f}</b>\n\n"
        f"💎 <b>3%</b> от каждого выигрыша реферала — вам на баланс!"
    )
    await safe_edit(call.message, text, reply_markup=referrals_menu(),
                    parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "ref:link")
async def ref_link(call: types.CallbackQuery):
    uid = call.from_user.id
    bot_info = await call.bot.get_me()
    link = f"https://t.me/{bot_info.username}?start=ref{uid}"
    await safe_answer(call.message, f"{LINK} <code>{link}</code>", parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "ref:top")
async def ref_top(call: types.CallbackQuery):
    top = db.get_top_wagered(10)
    text = f"{TOP} <b>Топ игроков:</b>\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, (uid, uname, wag) in enumerate(top, 1):
        medal = medals[i - 1] if i <= 3 else f"{i}."
        name = uname if uname else f"Юзер {uid}"
        text += (f"{medal} <a href='tg://user?id={uid}'>{name}</a> — "
                 f"<b>{wag:.2f}</b> {DOLLAR}\n")
    await safe_edit(call.message, text, reply_markup=referrals_menu(),
                    parse_mode="HTML")
    await call.answer()

# ============================================================
#              ВЫВОД РЕФ-БАЛАНСА
# ============================================================
@router.callback_query(F.data == "ref:withdraw")
async def ref_withdraw(call: types.CallbackQuery):
    uid = call.from_user.id
    amount = db.withdraw_ref_to_balance(uid)
    if amount <= 0:
        return await call.answer("❌ У тебя нет реферального баланса!",
                                 show_alert=True)
    new_bal = db.get_balance(uid)
    await call.answer(f"✅ Переведено {amount:.2f} USDT!", show_alert=True)
    try:
        await call.message.edit_text(
            f"✅ <b>Реферальный баланс переведён!</b>\n\n"
            f"💰 Переведено: <b>+{amount:.2f}</b> USDT\n"
            f"💼 Текущий баланс: <b>{new_bal:.2f}</b> USDT",
            parse_mode="HTML")
    except Exception:
        pass