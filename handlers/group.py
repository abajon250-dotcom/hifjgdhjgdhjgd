import asyncio
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.enums import ChatType
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from math_engine import calc_1_dice
from utils.emoji import DOLLAR

router = Router()

GROUP_FILTER = F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP})


# ============================================================
#              БАЗОВЫЕ КОМАНДЫ В ЧАТЕ (русские + английские)
# ============================================================
@router.message(GROUP_FILTER, Command("balance", "bal", "баланс", "бал"))
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
async def group_help(message: types.Message):
    await message.reply(
        "⚙️ <b>Команды в чате:</b>\n"
        "• /баланс — мой баланс\n"
        "• /топ — топ-5 игроков\n"
        "• /стата — моя статистика\n"
        "• /куб — играть в кубик\n"
        "• /помощь — эта справка",
        parse_mode="HTML"
    )


# ============================================================
#              ИГРА В КУБИК ПРЯМО В ЧАТЕ
# ============================================================
@router.message(GROUP_FILTER, Command("dice", "куб", "кубик", "дайс"))
async def group_dice(message: types.Message):
    if not message.from_user:
        return
    uid = message.from_user.id
    bet = db.get_bet(uid)

    if not db.has_enough(uid, bet):
        return await message.reply(
            f"❌ Недостаточно средств. Нужно <b>{bet}</b> {DOLLAR}\n"
            f"Баланс: <b>{db.get_balance(uid):.2f}</b>",
            parse_mode="HTML"
        )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Чёт (x1.9)", callback_data="g:d1:even",
                              style="primary"),
         InlineKeyboardButton(text="Нечёт (x1.9)", callback_data="g:d1:odd",
                              style="primary")],
        [InlineKeyboardButton(text="1-3 (x1.9)", callback_data="g:d1:1-3",
                              style="primary"),
         InlineKeyboardButton(text="4-6 (x1.9)", callback_data="g:d1:4-6",
                              style="primary")],
        [InlineKeyboardButton(text="Отмена", callback_data="g:cancel",
                              style="danger")],
    ])
    await message.reply(
        f"🎲 <a href='tg://user?id={uid}'>{message.from_user.full_name}</a> "
        f"ставит <b>{bet}</b> {DOLLAR}\n\n"
        f"<b>Выбери исход:</b>",
        reply_markup=kb, parse_mode="HTML"
    )


@router.callback_query(F.data == "g:cancel")
async def group_dice_cancel(call: types.CallbackQuery):
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.answer("Отменено")


@router.callback_query(F.data.startswith("g:d1:"))
async def group_dice_play(call: types.CallbackQuery):
    choice = call.data.split(":")[2]
    uid = call.from_user.id
    bet = db.get_bet(uid)

    if not db.has_enough(uid, bet):
        return await call.answer("❌ Недостаточно средств", show_alert=True)

    db.update_balance(uid, -bet)
    db.add_wager(uid, bet)
    db.inc_games(uid)

    try:
        await call.message.edit_text(
            f"🎲 Бросаю... Ставка: <b>{bet}</b> {DOLLAR}",
            parse_mode="HTML"
        )
    except Exception:
        pass
    await call.answer()

    m = await call.message.answer_dice(emoji="🎲")
    await asyncio.sleep(3.5)
    v = m.dice.value

    win, result = calc_1_dice(bet, choice, v)
    uname = call.from_user.full_name or "Игрок"
    mention = f'<a href="tg://user?id={uid}">{uname}</a>'

    if result == "win":
        db.update_balance(uid, win)
        db.add_win(uid, win)
        db.add_game(uid, "dice_1", bet, win, 2.0, "win")
        await call.message.reply(
            f"🎲 Выпало: <b>{v}</b>\n\n"
            f"🔼 {mention} выиграл <b>+{win:.2f}</b> {DOLLAR}",
            parse_mode="HTML"
        )
    else:
        db.add_loss(uid, bet)
        db.add_game(uid, "dice_1", bet, 0, 0, "lose")
        await call.message.reply(
            f"🎲 Выпало: <b>{v}</b>\n\n"
            f"🔽 {mention} проиграл <b>-{bet:.2f}</b> {DOLLAR}",
            parse_mode="HTML"
        )