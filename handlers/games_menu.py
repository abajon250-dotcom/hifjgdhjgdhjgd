from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from keyboards.inline import games_main, dice_menu
from utils.emoji import GAMES, DOLLAR, BET, WALLET, DICE

router = Router()


# ============================================================
#              ГЛАВНОЕ МЕНЮ ИГР
# ============================================================
def _games_text(uid):
    bal = db.get_balance(uid)
    bet = db.get_bet(uid)
    return (
        f"{GAMES} <b>Выбирайте игру для ставки!</b>\n\n"
        f"{BET} Ставка: <b>{bet}</b> {DOLLAR}\n"
        f"{WALLET} Баланс: <b>{bal:.2f}</b> {DOLLAR}"
    )


@router.callback_query(F.data == "games_main")
async def games_main_handler(call: types.CallbackQuery):
    await call.message.edit_text(_games_text(call.from_user.id),
                                 reply_markup=games_main(),
                                 parse_mode="HTML")
    await call.answer()


@router.message(F.text == "🎮 Играть")
async def btn_play(message: types.Message):
    await message.answer(_games_text(message.from_user.id),
                         reply_markup=games_main(),
                         parse_mode="HTML")


# ============================================================
#                    КУБИКИ
# ============================================================
@router.callback_query(F.data == "game:dice")
async def game_dice(call: types.CallbackQuery):
    await call.message.edit_text(
        "🎲 <b>Кубики</b>\n\nВыберите режим:",
        reply_markup=dice_menu(), parse_mode="HTML"
    )
    await call.answer()


# ============================================================
#                    СПОРТ — исходы
# ============================================================
def _choices_kb(items, prefix, back="games_main"):
    rows, row = [], []
    for text, code in items:
        row.append(InlineKeyboardButton(text=text, callback_data=f"{prefix}:{code}"))
        if len(row) == 2:
            rows.append(row); row = []
    if row: rows.append(row)
    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data=back)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


FOOTBALL_CHOICES = [
    ("Мимо ворот (x3)", "mimo"),
    ("В штангу (x4)", "shtanga"),
    ("Гол в центр (x2)", "center"),
    ("Гол от штанги (x3.5)", "from_shtanga"),
    ("Гол в угол (x1.8)", "corner"),
]

BASKET_CHOICES = [
    ("Отскок (x3)", "otskok"),
    ("Близко (x4)", "blizko"),
    ("Застрял (x5)", "zastryal"),
    ("Попал с краем (x2)", "edge"),
    ("Прямое попадание (x1.5)", "direct"),
]

DARTS_CHOICES = [
    ("Промах (x3)", "miss"),
    ("В центр (x5)", "bull"),
    ("Сектор 3 (x2.5)", "s3"),
    ("Сектор 4 (x2.5)", "s4"),
    ("Сектор 5 (x2.5)", "s5"),
    ("Сектор 6 (x2.5)", "s6"),
]

BOWLING_CHOICES = [
    ("Промах (x3.5)", "miss"),
    ("Сбито 1/6 (x4)", "p1"),
    ("Сбито 3/6 (x3)", "p3"),
    ("Сбито 4/6 (x2.5)", "p4"),
    ("Сбито 5/6 (x2)", "p5"),
    ("Страйк (x1.5)", "strike"),
]


@router.callback_query(F.data == "game:football")
async def game_football(call: types.CallbackQuery):
    await call.message.edit_text(
        "⚽ <b>Футбол — выберите исход:</b>",
        reply_markup=_choices_kb(FOOTBALL_CHOICES, "fc"),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "game:basketball")
async def game_basketball(call: types.CallbackQuery):
    await call.message.edit_text(
        "🏀 <b>Баскетбол — выберите исход:</b>",
        reply_markup=_choices_kb(BASKET_CHOICES, "bc"),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "game:darts")
async def game_darts(call: types.CallbackQuery):
    await call.message.edit_text(
        "🎯 <b>Дартс — выберите исход:</b>",
        reply_markup=_choices_kb(DARTS_CHOICES, "dc"),
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "game:bowling")
async def game_bowling(call: types.CallbackQuery):
    await call.message.edit_text(
        "🎳 <b>Боулинг — выберите исход:</b>",
        reply_markup=_choices_kb(BOWLING_CHOICES, "wc"),
        parse_mode="HTML"
    )
    await call.answer()


# ============================================================
#                    СЛОТЫ
# ============================================================
@router.callback_query(F.data == "game:slots")
async def game_slots(call: types.CallbackQuery):
    bet = db.get_bet(call.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Тройка (x30)", callback_data="sl:triple"),
         InlineKeyboardButton(text="✌️ Дубль (x3)", callback_data="sl:double")],
        [InlineKeyboardButton(text="🃏 Уникальные (x2)", callback_data="sl:unique")],
        [InlineKeyboardButton(text="7️⃣ x3 (x50)", callback_data="sl:exact_7️⃣")],
        [InlineKeyboardButton(text="🍇 x3 (x50)", callback_data="sl:exact_🍇")],
        [InlineKeyboardButton(text="🍋 x3 (x50)", callback_data="sl:exact_🍋")],
        [InlineKeyboardButton(text="BAR x3 (x50)", callback_data="sl:exact_BAR")],
        [InlineKeyboardButton(text="💥 7️⃣+BAR (x5)", callback_data="sl:combo")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="games_main")],
    ])
    await call.message.edit_text(
        f"🎰 <b>Слоты</b>\n{BET} Ставка: <b>{bet}</b> {DOLLAR}\n\nВыберите режим:",
        reply_markup=kb, parse_mode="HTML"
    )
    await call.answer()


# ============================================================
#                    РЕЖИМЫ
# ============================================================
@router.callback_query(F.data == "game:modes")
async def game_modes(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Турбо (скоро)", callback_data="mode:turbo")],
        [InlineKeyboardButton(text="🔄 Обычный", callback_data="mode:normal")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="games_main")],
    ])
    await call.message.edit_text(
        "🎮 <b>Режимы игры:</b>",
        reply_markup=kb, parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data == "mode:turbo")
async def mode_turbo(call: types.CallbackQuery):
    await call.answer("🚧 Турбо-режим в разработке", show_alert=True)


@router.callback_query(F.data == "mode:normal")
async def mode_normal(call: types.CallbackQuery):
    await call.answer("✅ Обычный режим активен", show_alert=True)


# ============================================================
#                    АВТОРСКИЕ ИГРЫ
# ============================================================
@router.callback_query(F.data == "game:custom")
async def game_custom(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💣 Мины",   callback_data="ar:mines"),
         InlineKeyboardButton(text="🗼 Башня",  callback_data="ar:tower")],
        [InlineKeyboardButton(text="🚀 Краш",   callback_data="ar:crash"),
         InlineKeyboardButton(text="🎯 Кено",   callback_data="ar:keno")],
        [InlineKeyboardButton(text="🎡 Рулетка", callback_data="ar:roulette")],
        [InlineKeyboardButton(text="🔙 Назад",   callback_data="games_main")],
    ])
    await call.message.edit_text(
        "🎨 <b>Авторские игры:</b>",
        reply_markup=kb, parse_mode="HTML"
    )
    await call.answer()


# ============================================================
#                    ИЗМЕНИТЬ СТАВКУ
# ============================================================
@router.callback_query(F.data == "game:set_bet")
async def game_set_bet(call: types.CallbackQuery):
    bet = db.get_bet(call.from_user.id)
    await call.answer(
        f"✏️ Текущая ставка: {bet}\n"
        f"Чтобы изменить — напиши в чат: ставка 0.2",
        show_alert=True
    )