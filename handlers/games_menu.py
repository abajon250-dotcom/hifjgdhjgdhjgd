from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from keyboards.inline import (games_main, dice_menu_1, dice_menu_2, dice_menu_3,
                              football_menu, basketball_menu, darts_menu,
                              bowling_menu, slots_menu, arcades_menu)
from utils.emoji import GAMES, DOLLAR, BET, WALLET, DICE

router = Router()


def _cb_uid(data):
    """Возвращает uid из callback_data (последний сегмент, если >5 цифр)."""
    parts = data.split(":")
    if parts and parts[-1].isdigit() and len(parts[-1]) > 5:
        return int(parts[-1])
    return None


def _check(call):
    """True если callback не твой."""
    uid = _cb_uid(call.data)
    if uid and uid != call.from_user.id:
        return True
    return False


def _games_text(uid):
    bal = db.get_balance(uid)
    bet = db.get_bet(uid)
    return (
        f"{GAMES} <b>Выбирайте игру для ставки!</b>\n\n"
        f"{BET} Ставка: <b>{bet}</b> {DOLLAR}\n"
        f"{WALLET} Баланс: <b>{bal:.2f}</b> {DOLLAR}"
    )


@router.callback_query(F.data.startswith("games_main"))
async def games_main_handler(call: types.CallbackQuery):
    if _check(call):
        return await call.answer("❌ Это не твоё меню!", show_alert=True)
    uid = call.from_user.id
    try:
        await call.message.edit_text(_games_text(uid),
                                     reply_markup=games_main(uid),
                                     parse_mode="HTML")
    except Exception:
        await call.message.answer(_games_text(uid),
                                  reply_markup=games_main(uid),
                                  parse_mode="HTML")
    await call.answer()


@router.message(F.text == "🎮 Играть")
async def btn_play(message: types.Message):
    uid = message.from_user.id
    await message.answer(_games_text(uid),
                         reply_markup=games_main(uid),
                         parse_mode="HTML")


# ============================================================
#                    КУБИКИ — открытие
# ============================================================
@router.callback_query(F.data.startswith("game:dice"))
async def game_dice(call: types.CallbackQuery):
    if _check(call):
        return await call.answer("❌ Это не твоя игра!", show_alert=True)
    uid = call.from_user.id
    await call.message.edit_text(
        "🎲 <b>Кубики</b>\n\nВыберите режим:",
        reply_markup=dice_menu_1(uid), parse_mode="HTML")
    await call.answer()


# ============================================================
#                    СПОРТ — открытие
# ============================================================
@router.callback_query(F.data.startswith("game:football"))
async def game_football(call: types.CallbackQuery):
    if _check(call):
        return await call.answer("❌ Это не твоя игра!", show_alert=True)
    uid = call.from_user.id
    await call.message.edit_text(
        "⚽ <b>Футбол — выберите исход:</b>",
        reply_markup=football_menu(uid), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("game:basketball"))
async def game_basketball(call: types.CallbackQuery):
    if _check(call):
        return await call.answer("❌ Это не твоя игра!", show_alert=True)
    uid = call.from_user.id
    await call.message.edit_text(
        "🏀 <b>Баскетбол — выберите исход:</b>",
        reply_markup=basketball_menu(uid), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("game:darts"))
async def game_darts(call: types.CallbackQuery):
    if _check(call):
        return await call.answer("❌ Это не твоя игра!", show_alert=True)
    uid = call.from_user.id
    await call.message.edit_text(
        "🎯 <b>Дартс — выберите исход:</b>",
        reply_markup=darts_menu(uid), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("game:bowling"))
async def game_bowling(call: types.CallbackQuery):
    if _check(call):
        return await call.answer("❌ Это не твоя игра!", show_alert=True)
    uid = call.from_user.id
    await call.message.edit_text(
        "🎳 <b>Боулинг — выберите исход:</b>",
        reply_markup=bowling_menu(uid), parse_mode="HTML")
    await call.answer()


# ============================================================
#                    СЛОТЫ — открытие
# ============================================================
@router.callback_query(F.data.startswith("game:slots"))
async def game_slots(call: types.CallbackQuery):
    if _check(call):
        return await call.answer("❌ Это не твоя игра!", show_alert=True)
    uid = call.from_user.id
    bet = db.get_bet(uid)
    await call.message.edit_text(
        f"🎰 <b>Слоты</b>\n{BET} Ставка: <b>{bet}</b> {DOLLAR}\n\nВыберите режим:",
        reply_markup=slots_menu(uid), parse_mode="HTML")
    await call.answer()


# ============================================================
#                    РЕЖИМЫ
# ============================================================
@router.callback_query(F.data.startswith("game:modes"))
async def game_modes(call: types.CallbackQuery):
    if _check(call):
        return await call.answer("❌ Это не твоя игра!", show_alert=True)
    uid = call.from_user.id
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Турбо (скоро)", callback_data=f"mode:turbo:{uid}")],
        [InlineKeyboardButton(text="🔄 Обычный", callback_data=f"mode:normal:{uid}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"games_main:{uid}")],
    ])
    await call.message.edit_text("🎮 <b>Режимы игры:</b>",
                                 reply_markup=kb, parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data.startswith("mode:turbo"))
async def mode_turbo(call: types.CallbackQuery):
    await call.answer("🚧 Турбо-режим в разработке", show_alert=True)


@router.callback_query(F.data.startswith("mode:normal"))
async def mode_normal(call: types.CallbackQuery):
    await call.answer("✅ Обычный режим активен", show_alert=True)


# ============================================================
#                    АВТОРСКИЕ ИГРЫ
# ============================================================
@router.callback_query(F.data.startswith("game:custom"))
async def game_custom(call: types.CallbackQuery):
    if _check(call):
        return await call.answer("❌ Это не твоя игра!", show_alert=True)
    uid = call.from_user.id
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💣 Мины", callback_data=f"ar:mines:{uid}"),
         InlineKeyboardButton(text="🗼 Башня", callback_data=f"ar:tower:{uid}")],
        [InlineKeyboardButton(text="🚀 Краш", callback_data=f"ar:crash:{uid}"),
         InlineKeyboardButton(text="🎯 Кено", callback_data=f"ar:keno:{uid}")],
        [InlineKeyboardButton(text="🎡 Рулетка", callback_data=f"ar:roulette:{uid}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"games_main:{uid}")],
    ])
    await call.message.edit_text("🎨 <b>Авторские игры:</b>",
                                 reply_markup=kb, parse_mode="HTML")
    await call.answer()


# ============================================================
#                    ИЗМЕНИТЬ СТАВКУ
# ============================================================
@router.callback_query(F.data.startswith("game:set_bet"))
async def game_set_bet(call: types.CallbackQuery):
    bet = db.get_bet(call.from_user.id)
    await call.answer(
        f"✏️ Текущая ставка: {bet}\n"
        f"Чтобы изменить — напиши в чат: 5$",
        show_alert=True)