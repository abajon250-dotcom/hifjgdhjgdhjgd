import os
import time
from datetime import datetime, timezone
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from utils.emoji import DOLLAR, PERCENT, WALLET, BONUS, PROFILE, TURNOVER, DICE

router = Router()
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))


def is_admin(uid: int) -> bool:
    return uid == ADMIN_ID


class AdminState(StatesGroup):
    waiting_broadcast    = State()
    waiting_user_id      = State()
    waiting_balance_amt  = State()
    waiting_promo_code   = State()
    waiting_promo_amount = State()
    waiting_promo_uses   = State()


# ============================================================
#                    КЛАВИАТУРА
# ============================================================
def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Обновить", callback_data="admin_refresh"),
         InlineKeyboardButton(text="💰 Казна", callback_data="admin_treasury",
                              style="success")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users"),
         InlineKeyboardButton(text="🎁 Создать промокод",
                              callback_data="admin_promo", style="success")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="💰 Выдать", callback_data="admin_give"),
         InlineKeyboardButton(text="💸 Забрать", callback_data="admin_take")],
        [InlineKeyboardButton(text="🚫 Бан / Разбан", callback_data="admin_ban")],
    ])


async def build_admin_text() -> str:
    now = int(time.time())
    day_start = now - (now % 86400)
    s = db.get_admin_stats(day_start)
    top = db.get_top_players_today(day_start, 5)

    top_text = ""
    for i, (uid, t) in enumerate(top, 1):
        top_text += f"{i}. <code>{uid}</code> — {t:.2f}\n"
    if not top_text:
        top_text = "—\n"

    return (
        f"👑 <b>АДМИН-ПАНЕЛЬ</b>\n"
        f"<i>{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</i>\n\n"

        f"📊 <b>За сегодня:</b>\n"
        f"  {DICE} Игр: <b>{s['games_today']}</b>\n"
        f"  {TURNOVER} Оборот: <b>{s['turnover_today']:.2f}</b>\n"
        f"  {DOLLAR} Выплаты: <b>{s['payout_today']:.2f}</b>\n"
        f"  {PERCENT} Профит: <b>{s['profit_today']:.2f}</b>\n"
        f"  {WALLET} Депозитов: <b>{s['dep_today']:.2f}</b> ({s['dep_count']})\n"
        f"  💸 Выводов: <b>{s['wd_today']:.2f}</b> ({s['wd_count']})\n\n"

        f"🌍 <b>За всё время:</b>\n"
        f"  {PROFILE} Юзеров: <b>{s['users_count']}</b>\n"
        f"  {TURNOVER} Общий оборот: <b>{s['total_turnover']:.2f}</b>\n"
        f"  💼 В кошельках: <b>{s['total_balances']:.2f}</b>\n\n"

        f"🏆 <b>ТОП-5 за сегодня:</b>\n{top_text}"
    )


# ============================================================
#                    ОТКРЫТИЕ
# ============================================================
@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(await build_admin_text(),
                         reply_markup=admin_kb(), parse_mode="HTML")


@router.message(F.text == "👑 Админка")
async def btn_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(await build_admin_text(),
                         reply_markup=admin_kb(), parse_mode="HTML")


@router.callback_query(F.data == "admin_panel")
async def cb_admin_panel(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("Нет доступа", show_alert=True)
    text = await build_admin_text()
    try:
        await call.message.edit_text(text, reply_markup=admin_kb(), parse_mode="HTML")
    except Exception:
        await call.message.answer(text, reply_markup=admin_kb(), parse_mode="HTML")
    await call.answer()


@router.callback_query(F.data == "admin_refresh")
async def admin_refresh(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("Нет доступа", show_alert=True)
    try:
        await call.message.edit_text(await build_admin_text(),
                                     reply_markup=admin_kb(), parse_mode="HTML")
    except Exception:
        pass
    await call.answer("Обновлено")


# ============================================================
#                    ПРОМОКОД
# ============================================================
@router.callback_query(F.data == "admin_promo")
async def admin_promo(call: types.CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer("Нет доступа", show_alert=True)
    await call.message.answer("Введите код промокода (без пробелов):")
    await state.set_state(AdminState.waiting_promo_code)
    await call.answer()


@router.message(AdminState.waiting_promo_code)
async def promo_code(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(code=message.text.strip())
    await message.answer("Введите сумму бонуса (USDT):")
    await state.set_state(AdminState.waiting_promo_amount)


@router.message(AdminState.waiting_promo_amount)
async def promo_amount(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        amount = float(message.text.replace(",", "."))
    except Exception:
        return await message.answer("❌ Введите число")
    await state.update_data(amount=amount)
    await message.answer("Сколько использований?")
    await state.set_state(AdminState.waiting_promo_uses)


@router.message(AdminState.waiting_promo_uses)
async def promo_uses(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        uses = int(message.text.strip())
    except Exception:
        return await message.answer("❌ Целое число")

    data = await state.get_data()
    db.create_promo(data["code"], data["amount"], uses)
    await message.answer(
        f"✅ Промокод <code>{data['code']}</code> на <b>{data['amount']}</b> USDT,\n"
        f"Использований: <b>{uses}</b>",
        parse_mode="HTML"
    )
    await state.clear()


# ============================================================
#                    РАССЫЛКА
# ============================================================
@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(call: types.CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer("Нет доступа", show_alert=True)
    await call.message.answer("Введите текст рассылки (поддерживается HTML):")
    await state.set_state(AdminState.waiting_broadcast)
    await call.answer()


@router.message(AdminState.waiting_broadcast)
async def do_broadcast(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    text = message.html_text
    db.cursor.execute("SELECT user_id FROM users WHERE is_banned = 0")
    users = db.cursor.fetchall()

    sent, failed = 0, 0
    status = await message.answer(f"📢 Начинаю... 0/{len(users)}")

    for i, (uid,) in enumerate(users, 1):
        try:
            await message.bot.send_message(uid, text, parse_mode="HTML")
            sent += 1
        except Exception:
            failed += 1
        if i % 20 == 0:
            try:
                await status.edit_text(
                    f"📢 {i}/{len(users)} | ✅{sent} ❌{failed}"
                )
            except Exception:
                pass

    await status.edit_text(
        f"✅ Готово!\nОтправлено: <b>{sent}</b>\nОшибок: <b>{failed}</b>",
        parse_mode="HTML"
    )
    await state.clear()


# ============================================================
#                    ВЫДАТЬ / ЗАБРАТЬ / БАН
# ============================================================
@router.callback_query(F.data == "admin_give")
async def admin_give(call: types.CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer("Нет доступа", show_alert=True)
    await call.message.answer("Введите ID пользователя:")
    await state.update_data(action="give")
    await state.set_state(AdminState.waiting_user_id)
    await call.answer()


@router.callback_query(F.data == "admin_take")
async def admin_take(call: types.CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer("Нет доступа", show_alert=True)
    await call.message.answer("Введите ID пользователя:")
    await state.update_data(action="take")
    await state.set_state(AdminState.waiting_user_id)
    await call.answer()


@router.callback_query(F.data == "admin_ban")
async def admin_ban(call: types.CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return await call.answer("Нет доступа", show_alert=True)
    await call.message.answer("Введите ID пользователя (бан/разбан):")
    await state.update_data(action="ban")
    await state.set_state(AdminState.waiting_user_id)
    await call.answer()


@router.message(AdminState.waiting_user_id)
async def admin_uid(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        target = int(message.text.strip())
    except Exception:
        return await message.answer("❌ ID должен быть числом")

    data = await state.get_data()
    action = data.get("action")

    if action == "ban":
        if db.is_banned(target):
            db.unban_user(target)
            await message.answer(f"✅ <code>{target}</code> разбанен.", parse_mode="HTML")
        else:
            db.ban_user(target)
            await message.answer(f"🚫 <code>{target}</code> забанен.", parse_mode="HTML")
        await state.clear()
        return

    await state.update_data(target=target)
    await message.answer(f"ID: <code>{target}</code>\nВведите сумму (USDT):",
                         parse_mode="HTML")
    await state.set_state(AdminState.waiting_balance_amt)


@router.message(AdminState.waiting_balance_amt)
async def admin_balance_amt(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        amount = float(message.text.replace(",", "."))
    except Exception:
        return await message.answer("❌ Введите число")

    data = await state.get_data()
    target = data["target"]
    action = data["action"]

    if action == "give":
        db.update_balance(target, amount)
        await message.answer(
            f"✅ Выдано <b>{amount}</b> USDT → <code>{target}</code>\n"
            f"Новый баланс: <b>{db.get_balance(target):.2f}</b>",
            parse_mode="HTML"
        )
        try:
            await message.bot.send_message(
                target,
                f"🎁 Вам выдан бонус <b>{amount}</b> USDT!",
                parse_mode="HTML"
            )
        except Exception:
            pass
    else:
        db.update_balance(target, -amount)
        await message.answer(
            f"✅ Списано <b>{amount}</b> USDT у <code>{target}</code>\n"
            f"Новый баланс: <b>{db.get_balance(target):.2f}</b>",
            parse_mode="HTML"
        )
    await state.clear()


# ============================================================
#                    СПИСОК ЮЗЕРОВ
# ============================================================
@router.callback_query(F.data == "admin_users")
async def admin_users(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("Нет доступа", show_alert=True)

    db.cursor.execute(
        "SELECT user_id, username, balance, total_wagered "
        "FROM users ORDER BY total_wagered DESC LIMIT 15"
    )
    users = db.cursor.fetchall()

    text = "👥 <b>ТОП-15 по обороту:</b>\n\n"
    for i, (uid, uname, bal, wag) in enumerate(users, 1):
        text += (f"{i}. <code>{uid}</code> @{uname or '—'}\n"
                 f"   💵 {bal:.2f} | 📉 {wag:.2f}\n")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_refresh")]
    ])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await call.answer()

# ============================================================
#              КАЗНА
# ============================================================
@router.callback_query(F.data == "admin_treasury")
async def admin_treasury(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        return await call.answer("Нет доступа", show_alert=True)

    await call.answer("⏳ Считаю казну...", show_alert=False)

    from utils.treasury import get_treasury
    try:
        t = await get_treasury()
    except Exception as e:
        return await call.message.answer(f"❌ Ошибка: {e}")

    # Определяем статус резерва
    if t["reserve"] >= 0:
        status = "🟢 <b>Казна в плюсе</b>"
    else:
        status = "🔴 <b>ВНИМАНИЕ: резерва не хватает!</b>"

    text = (
        f"💰 <b>КАЗНА КАЗИНО</b>\n\n"

        f"<b>💳 Платёжные системы:</b>\n"
        f"  🏦 CryptoBot: <b>{t['crypto']:.2f}</b> USDT\n"
        f"  ℹ️ xRocket: <b>{t['xrocket']:.2f}</b> USDT\n"
        f"  📊 Всего на платёжках: <b>{t['total_on_platforms']:.2f}</b> USDT\n\n"

        f"<b>👥 Обязательства перед юзерами:</b>\n"
        f"  💼 На балансах: <b>{t['users_balance']:.2f}</b> USDT\n\n"

        f"<b>📈 Статистика:</b>\n"
        f"  ⬇️ Пополнено: <b>{t['deposited']:.2f}</b>\n"
        f"  ⬆️ Выведено: <b>{t['withdrawn']:.2f}</b>\n"
        f"  📉 Оборот: <b>{t['wagered']:.2f}</b>\n"
        f"  💸 Выиграно юзерам: <b>{t['won']:.2f}</b>\n\n"

        f"<b>💵 Итог:</b>\n"
        f"  💰 Профит казино: <b>{t['profit']:.2f}</b> USDT\n"
        f"  🏦 Резерв (платёжки − обязательства): "
        f"<b>{t['reserve']:.2f}</b> USDT\n\n"

        f"{status}"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_treasury",
                              style="success")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_refresh",
                              style="danger")],
    ])

    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await call.message.answer(text, reply_markup=kb, parse_mode="HTML")