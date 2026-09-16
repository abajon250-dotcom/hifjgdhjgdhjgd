import asyncio
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from keyboards.inline import (football_menu, basketball_menu,
                              darts_menu, bowling_menu)
from math_engine import calc_football, calc_basketball, calc_darts, calc_bowling
from utils.emoji import DOLLAR

router = Router()


# ============================================================
#                    ОТКРЫТИЕ МЕНЮ
# ============================================================
@router.callback_query(F.data == "game:football")
async def menu_football(call: types.CallbackQuery):
    await call.message.edit_text("⚽ <b>Выберите исход игры!</b>",
                                 reply_markup=football_menu(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "game:basketball")
async def menu_basket(call: types.CallbackQuery):
    await call.message.edit_text("🏀 <b>Выберите исход игры!</b>",
                                 reply_markup=basketball_menu(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "game:darts")
async def menu_darts(call: types.CallbackQuery):
    await call.message.edit_text("🎯 <b>Выберите исход игры!</b>",
                                 reply_markup=darts_menu(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "game:bowling")
async def menu_bowling(call: types.CallbackQuery):
    await call.message.edit_text("🎳 <b>Выберите исход игры!</b>",
                                 reply_markup=bowling_menu(), parse_mode="HTML")
    await call.answer()


# ============================================================
#                    ЗАПУСК
# ============================================================
@router.callback_query(F.data.startswith("fc:"))
async def play_football(call: types.CallbackQuery):
    await _play(call, "football", call.data.split(":", 1)[1])


@router.callback_query(F.data.startswith("bc:"))
async def play_basket(call: types.CallbackQuery):
    await _play(call, "basketball", call.data.split(":", 1)[1])


@router.callback_query(F.data.startswith("dc:"))
async def play_darts(call: types.CallbackQuery):
    await _play(call, "darts", call.data.split(":", 1)[1])


@router.callback_query(F.data.startswith("wc:"))
async def play_bowling(call: types.CallbackQuery):
    await _play(call, "bowling", call.data.split(":", 1)[1])


async def _play(call: types.CallbackQuery, game: str, choice: str):
    uid = call.from_user.id
    bet = db.get_bet(uid)

    if not db.has_enough(uid, bet):
        return await call.answer(
            f"❌ Нужно {bet} 💵. Баланс: {db.get_balance(uid):.2f}",
            show_alert=True
        )

    db.update_balance(uid, -bet)
    db.add_wager(uid, bet)
    db.inc_games(uid)

    emoji_map = {
        "football": "⚽",
        "basketball": "🏀",
        "darts": "🎯",
        "bowling": "🎳",
    }
    emoji = emoji_map[game]

    await call.message.edit_text(
        f"{emoji} Играем... Ставка: <b>{bet}</b> {DOLLAR}",
        parse_mode="HTML"
    )
    await call.answer()

    m = await call.message.answer_dice(emoji=emoji)
    await asyncio.sleep(3.5)
    v = m.dice.value

    if game == "football":
        win, result = calc_football(bet, choice, v)
    elif game == "basketball":
        win, result = calc_basketball(bet, choice, v)
    elif game == "darts":
        win, result = calc_darts(bet, choice, v)
    else:
        win, result = calc_bowling(bet, choice, v)

    back_cb = {
        "football": "game:football",
        "basketball": "game:basketball",
        "darts": "game:darts",
        "bowling": "game:bowling",
    }[game]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Ещё раз", callback_data=back_cb)],
        [InlineKeyboardButton(text="🏠 Главная", callback_data="back_to_main")],
    ])

    if result == "win":
        db.update_balance(uid, win)
        db.add_win(uid, win)
        db.add_game(uid, f"sport_{game}", bet, win, win / bet if bet else 0, "win")
        await call.message.answer(
            f"{emoji} Выпало: <b>{v}</b>\n\n"
            f"✅ <b>Выигрыш!</b>\n"
            f"{DOLLAR} +{win:.2f}\n"
            f"💼 Баланс: <b>{db.get_balance(uid):.2f}</b>",
            reply_markup=kb, parse_mode="HTML"
        )
    else:
        db.add_loss(uid, bet)
        db.add_game(uid, f"sport_{game}", bet, 0, 0, "lose")
        await call.message.answer(
            f"{emoji} Выпало: <b>{v}</b>\n\n"
            f"❌ <b>Проигрыш</b>\n"
            f"-{bet} {DOLLAR}\n"
            f"💼 Баланс: <b>{db.get_balance(uid):.2f}</b>",
            reply_markup=kb, parse_mode="HTML"
        )