import random
import string
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from utils.emoji import DOLLAR, WALLET, REF, LINK, BET, CHECK_OK
from utils.user_state import get_bet

router = Router()
ADMIN_ID = int(__import__("os").getenv("ADMIN_ID", 0))


def _gen_code(n=8):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=n))


class SocialState(StatesGroup):
    waiting_transfer_amount = State()
    waiting_transfer_user = State()
    waiting_promo_amount = State()
    waiting_promo_uses = State()
    waiting_check_amount = State()
    waiting_chat_link = State()


# ============================================================
#              ПЕРЕВОД БАЛАНСА
# ============================================================
@router.message(F.text.regexp(r"(?i)^(перевод|отправить|перевести)\s+([\d.,]+)(\s+.*)?$"))
async def transfer_start(message: types.Message, state: FSMContext):
    import re
    m = re.search(r"([\d.,]+)", message.text)
    if not m:
        return
    try:
        amount = float(m.group(1).replace(",", "."))
        if amount <= 0:
            raise ValueError
    except Exception:
        return await message.answer("❌ Формат: <code>перевод 5 @юзер</code>",
                                    parse_mode="HTML")

    uid = message.from_user.id
    bal = db.get_balance(uid)
    if amount > bal:
        return await message.answer(
            f"❌ <b>Недостаточно средств</b>\n\n"
            f"{DOLLAR} Баланс: <b>{bal:.2f}</b>",
            parse_mode="HTML")

    # ищем юзернейм в тексте
    parts = message.text.split()
    target = None
    for p in parts:
        if p.startswith("@"):
            target = p[1:]
            break

    if not target:
        # если это reply — берём того, кому отвечаем
        if message.reply_to_message and message.reply_to_message.from_user:
            tu = message.reply_to_message.from_user
            await _do_transfer(message, uid, tu.id, amount, tu.full_name)
            return
        await state.update_data(amount=amount)
        await message.answer(
            f"💸 <b>Перевод {amount:.2f} {DOLLAR}</b>\n\n"
            f"Напиши <b>@юзернейм</b> получателя или ответь на его сообщение.",
            parse_mode="HTML")
        await state.set_state(SocialState.waiting_transfer_user)
        return

    # ищем по username
    row = db.cursor.execute(
        "SELECT user_id, username FROM users WHERE username LIKE ?",
        (f"%{target}%",)).fetchone()
    if not row:
        return await message.answer(
            f"❌ Пользователь <b>@{target}</b> не найден.\n"
            f"Попроси его написать /start боту.", parse_mode="HTML")
    await _do_transfer(message, uid, row[0], amount, row[1])


@router.message(SocialState.waiting_transfer_user)
async def transfer_target(message: types.Message, state: FSMContext):
    data = await state.get_data()
    amount = data["amount"]
    uid = message.from_user.id

    if message.reply_to_message and message.reply_to_message.from_user:
        tu = message.reply_to_message.from_user
        await _do_transfer(message, uid, tu.id, amount, tu.full_name)
        await state.clear()
        return

    text = (message.text or "").strip().lstrip("@")
    row = db.cursor.execute(
        "SELECT user_id, username FROM users WHERE username LIKE ?",
        (f"%{text}%",)).fetchone()
    if not row:
        return await message.answer(f"❌ @{text} не найден.")
    await _do_transfer(message, uid, row[0], amount, row[1])
    await state.clear()


async def _do_transfer(message, from_uid, to_uid, amount, to_name):
    ok, err = db.transfer_balance(from_uid, to_uid, amount)
    if not ok:
        errs = {
            "self": "❌ Себе переводить нельзя.",
            "amount": "❌ Неверная сумма.",
            "no_money": "❌ Недостаточно средств.",
        }
        return await message.answer(errs.get(err, "❌ Ошибка."), parse_mode="HTML")

    new_bal = db.get_balance(from_uid)
    await message.answer(
        f"{CHECK_OK} <b>Перевод выполнен!</b>\n\n"
        f"💸 Отправлено: <b>{amount:.2f}</b> {DOLLAR}\n"
        f"👤 Кому: <b>{to_name}</b>\n"
        f"{WALLET} Баланс: <b>{new_bal:.2f}</b> {DOLLAR}",
        parse_mode="HTML")

    try:
        await message.bot.send_message(
            to_uid,
            f"{CHECK_OK} <b>Вам перевели {amount:.2f} {DOLLAR}!</b>\n\n"
            f"👤 От: <b>{message.from_user.full_name}</b>\n"
            f"{WALLET} Баланс: <b>{db.get_balance(to_uid):.2f}</b>",
            parse_mode="HTML")
    except Exception:
        pass


# ============================================================
#              СОЗДАНИЕ ПРОМОКОДА ОТ ЮЗЕРА
# ============================================================
@router.message(F.text.regexp(r"(?i)^создатьпромо\s+([\d.,]+)\s+(\d+)$"))
async def create_user_promo(message: types.Message):
    import re
    m = re.search(r"([\d.,]+)\s+(\d+)", message.text)
    if not m:
        return
    try:
        amount = float(m.group(1).replace(",", "."))
        uses = int(m.group(2))
        if amount <= 0 or uses <= 0:
            raise ValueError
    except Exception:
        return await message.answer(
            "❌ Формат: <code>создатьпромо 5 10</code>\n"
            "(сумма каждой активации и кол-во активаций)", parse_mode="HTML")

    uid = message.from_user.id
    total = round(amount * uses, 2)
    bal = db.get_balance(uid)
    if total > bal:
        return await message.answer(
            f"❌ <b>Недостаточно средств</b>\n\n"
            f"Нужно: <b>{total:.2f}</b> {DOLLAR}\n"
            f"Баланс: <b>{bal:.2f}</b> {DOLLAR}",
            parse_mode="HTML")

    code = _gen_code(8)
    ok, res = db.create_user_promo(code, uid, amount, uses)
    if not ok:
        return await message.answer("❌ Не удалось создать промокод.",
                                    parse_mode="HTML")

    bot_info = await message.bot.get_me()
    link = f"https://t.me/{bot_info.username}?start=promo_{code}"

    await message.answer(
        f"{CHECK_OK} <b>Промокод создан!</b>\n\n"
        f"🔑 Код: <code>{code}</code>\n"
        f"💰 Сумма активации: <b>{amount:.2f}</b> {DOLLAR}\n"
        f"👥 Активаций: <b>{uses}</b>\n"
        f"💸 С баланса списано: <b>{total:.2f}</b> {DOLLAR}\n\n"
        f"🔗 Ссылка для рассылки:\n<code>{link}</code>\n\n"
        f"Отправь её друзьям — они получат <b>{amount:.2f}</b> {DOLLAR}!",
        parse_mode="HTML")


@router.message(F.text.regexp(r"(?i)^моипромо$"))
async def my_promos(message: types.Message):
    uid = message.from_user.id
    try:
        db.cursor.execute(
            "SELECT code, amount, uses_left FROM user_promos WHERE owner_id=?",
            (uid,))
        rows = db.cursor.fetchall()
    except Exception:
        rows = []
    if not rows:
        return await message.answer(
            "❌ У тебя нет созданных промокодов.\n\n"
            "Создай: <code>создатьпромо 5 10</code>", parse_mode="HTML")
    text = "🎁 <b>Твои промокоды:</b>\n\n"
    for code, amt, left in rows:
        text += f"🔑 <code>{code}</code> — {amt:.2f}$ × {left} активаций\n"
    await message.answer(text, parse_mode="HTML")


# ============================================================
#              ЧЕКИ
# ============================================================
@router.message(F.text.regexp(r"(?i)^чек\s+([\d.,]+)$"))
async def create_check(message: types.Message):
    import re
    m = re.search(r"([\d.,]+)", message.text)
    if not m:
        return
    try:
        amount = float(m.group(1).replace(",", "."))
        if amount <= 0:
            raise ValueError
    except Exception:
        return await message.answer("❌ Формат: <code>чек 25</code>",
                                    parse_mode="HTML")

    uid = message.from_user.id
    bal = db.get_balance(uid)
    if amount > bal:
        return await message.answer(
            f"❌ <b>Недостаточно средств</b>\n\n"
            f"Нужно: <b>{amount:.2f}</b> {DOLLAR}\n"
            f"Баланс: <b>{bal:.2f}</b> {DOLLAR}",
            parse_mode="HTML")

    code = _gen_code(10)
    if not db.create_check(code, uid, amount):
        return await message.answer("❌ Не удалось создать чек.")

    bot_info = await message.bot.get_me()
    link = f"https://t.me/{bot_info.username}?start=check_{code}"

    await message.answer(
        f"{CHECK_OK} <b>Чек на {amount:.2f} {DOLLAR} создан!</b>\n\n"
        f"🔗 Ссылка:\n<code>{link}</code>\n\n"
        f"📌 Когда кто-то активирует — он получит <b>{amount:.2f}</b> {DOLLAR} "
        f"и станет твоим рефералом!",
        parse_mode="HTML")


# ============================================================
#              МОЙ ЧАТ (реферальная ссылка через свой чат)
# ============================================================
@router.message(F.text.regexp(r"(?i)^мойчат$"))
async def my_chat(message: types.Message, state: FSMContext):
    uid = message.from_user.id
    link = db.get_my_chat_link(uid)
    if link:
        bot_info = await message.bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start=chat{uid}"
        await message.answer(
            f"📢 <b>Твой чат:</b> {link}\n\n"
            f"🔗 <b>Реферальная ссылка для чата:</b>\n<code>{ref_link}</code>\n\n"
            f"Кто зайдёт по ней — станет твоим рефералом!\n\n"
            f"Хочешь изменить ссылку — напиши:\n"
            f"<code>мойчат https://t.me/твой_чат</code>",
            parse_mode="HTML")
        return
    await message.answer(
        "📢 <b>Добавь свой чат</b>\n\n"
        "Напиши: <code>мойчат https://t.me/твой_чат</code>",
        parse_mode="HTML")
    await state.set_state(SocialState.waiting_chat_link)


@router.message(F.text.regexp(r"(?i)^мойчат\s+(.+)$"))
async def set_my_chat(message: types.Message):
    import re
    m = re.search(r"мойчат\s+(.+)", message.text, re.IGNORECASE)
    link = m.group(1).strip()
    uid = message.from_user.id
    db.set_my_chat_link(uid, link)

    bot_info = await message.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=chat{uid}"
    await message.answer(
        f"{CHECK_OK} <b>Чат сохранён!</b>\n\n"
        f"📢 {link}\n\n"
        f"🔗 <b>Твоя реф-ссылка:</b>\n<code>{ref_link}</code>\n\n"
        f"Кто зайдёт — твой реферал!",
        parse_mode="HTML")