import asyncio
import random
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from keyboards.inline import slots_menu
from math_engine import spin_slots, calc_slots
from utils.emoji import DOLLAR

router = Router()

SYMBOLS = ["7️⃣", "🍇", "🍋", "BAR", "🔔", "💎"]


@router.callback_query(F.data == "game:slots")
async def slots_open(call: types.CallbackQuery):
    bet = db.get_bet(call.from_user.id)
    await call.message.edit_text(
        f"🎰 <b>Выберите исход игры!</b>\n\n"
        f"Ставка: <b>{bet}</b> {DOLLAR}",
        reply_markup=slots_menu(), parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(F.data.startswith("sl:"))
async def slots_play(call: types.CallbackQuery):
    choice = call.data.split(":", 1)[1]
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

    msg = await call.message.edit_text("🎰 | ❓ | ❓ | ❓ |")
    await call.answer()

    # Анимация
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
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Ещё раз", callback_data="game:slots")],
        [InlineKeyboardButton(text="🏠 Главная", callback_data="back_to_main")],
    ])
    reels_str = f"{reels[0]} | {reels[1]} | {reels[2]}"

    if result == "win":
        db.update_balance(uid, win)
        db.add_win(uid, win)
        db.add_game(uid, "slots", bet, win, win / bet if bet else 0, "win")
        await call.message.answer(
            f"🎰 <b>{reels_str}</b>\n\n"
            f"✅ <b>Выигрыш!</b>\n"
            f"{DOLLAR} +{win:.2f}\n"
            f"💼 Баланс: <b>{db.get_balance(uid):.2f}</b>",
            reply_markup=kb, parse_mode="HTML"
        )
    else:
        db.add_loss(uid, bet)
        db.add_game(uid, "slots", bet, 0, 0, "lose")
        await call.message.answer(
            f"🎰 <b>{reels_str}</b>\n\n"
            f"❌ <b>Проигрыш</b>\n"
            f"-{bet} {DOLLAR}\n"
            f"💼 Баланс: <b>{db.get_balance(uid):.2f}</b>",
            reply_markup=kb, parse_mode="HTML"
        )