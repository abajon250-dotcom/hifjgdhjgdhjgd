import os
import logging
from aiogram import Bot

log = logging.getLogger(__name__)

SOURCE_ID = os.getenv("SOURCE_CHANNEL_ID")           # CatHome | Game
TARGET_ID = os.getenv("WIN_NOTIFY_CHANNEL")          # CatHome | BETS
MIN_WIN = float(os.getenv("WIN_NOTIFY_MIN", 10))


CHOICE_TEXT = {
    "even": "Чёт", "odd": "Нечёт",
    "less": "Меньше 4", "more": "Больше 3",
    "numbers": "Числа", "no_numbers": "Без чисел",
    "ladder1": "Лесенка 1", "ladder2": "Лесенка 2",
    "double": "Дубль", "sum_prod": "Сумма/Произведение",
    "corridor": "Коридор", "sniper": "Снайпер", "lift": "Лифт",
    "sum7_less": "Сумма < 7", "sum7_greater": "Сумма > 7", "sum7_exact": "Сумма = 7",
    "three_even": "Три чёт", "three_odd": "Три нечет",
    "triple": "Трипл", "unique": "Уникальные",
    "straight": "Стрит", "combination": "Комбинация",
    "greater_10": "Сумма > 10", "less_11": "Сумма < 11",
    "big": "Большой куб",
}


def _choice_label(choice: str) -> str:
    if choice in CHOICE_TEXT:
        return CHOICE_TEXT[choice]
    if choice.startswith("num"):
        return f"Число {choice[3:]}"
    if choice.startswith("exact_"):
        return f"Точное {choice.split('_')[1]}"
    if choice.startswith("prod_"):
        return f"Произведение ≥ {choice.split('_')[1]}"
    return choice


async def notify_result(bot: Bot, uid: int, username: str, game: str,
                        choice: str, bet: float, win: float,
                        mult: float, balance: float, is_win: bool):
    """Отправляет результат: пишет в SOURCE, потом пересылает в TARGET."""
    if not SOURCE_ID or not TARGET_ID:
        log.warning("[notify] SOURCE_CHANNEL_ID или WIN_NOTIFY_CHANNEL не заданы")
        return

    if win < MIN_WIN and bet < MIN_WIN:
        return

    mention = f'<a href="tg://user?id={uid}">@{username or "player"}</a>'
    label = _choice_label(choice)

    if is_win:
        header = f"😎 {mention}, выиграл <b>{win:.2f}</b>💲"
    else:
        header = f"😎 {mention}, проиграл <b>{bet:.2f}</b>💲"

    text = (
        f"{header}\n\n"
        f"<blockquote>🎲 {game} — {label} × {mult:.2f}</blockquote>\n\n"
        f"Ставка: <b>{bet:.2f}</b>💲\n"
        f"Баланс: <b>{balance:.2f}</b>💲"
    )

    try:
        # 1. Отправляем в SOURCE (CatHome | Game)
        msg = await bot.send_message(int(SOURCE_ID), text, parse_mode="HTML")
        # 2. Пересылаем в TARGET (CatHome | BETS)
        await bot.forward_message(
            chat_id=int(TARGET_ID),
            from_chat_id=int(SOURCE_ID),
            message_id=msg.message_id
        )
        # 3. Удаляем из SOURCE, чтобы не засорять
        try:
            await bot.delete_message(int(SOURCE_ID), msg.message_id)
        except Exception:
            pass

        log.info(f"[notify] Отправлен результат {username}")
    except Exception as e:
        log.error(f"[notify_result] {e}")


async def notify_win(bot, uid, username, game, bet, win, mult, balance=None):
    await notify_result(bot, uid, username, game, "", bet, win, mult,
                        balance or 0.0, True)


async def notify_big_bet(bot, uid, username, game, bet):
    pass