import os
import logging
from aiogram import Bot

log = logging.getLogger(__name__)


def _get_ids():
    """Читает ID каналов при каждом вызове — env точно загружен."""
    return (
        os.getenv("SOURCE_CHANNEL_ID"),
        os.getenv("WIN_NOTIFY_CHANNEL"),
        float(os.getenv("WIN_NOTIFY_MIN", 0.5)),
    )


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
    # Спорт
    "clean": "Чистый гол", "any": "Любой гол", "stuck": "Застрял мяч",
    "miss": "Промах", "center": "Центр", "red": "Красный",
    "white": "Белый", "bounce": "Отскок", "nine": "Девятка",
    "bar": "Штанга", "strike": "Страйк",
    "otskok": "Отскок", "blizko": "Близко", "zastryal": "Застрял",
    "edge": "С краем", "direct": "Прямое",
    # Слоты
    "777": "777", "77x": "77*", "any_sl": "Любая комбинация",
    "lucky7": "Лаки 7", "lines": "Линии", "sum": "Сумма",
    "piggy": "Копилка", "ladder": "Лесенка",
}


def _label(choice: str) -> str:
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
    source_id, target_id, min_win = _get_ids()

    log.info(f"[notify] source={source_id} target={target_id} min={min_win}")
    log.info(f"[notify] bet={bet} win={win} game={game}")

    if not source_id or not target_id:
        log.warning("[notify] SOURCE_CHANNEL_ID или WIN_NOTIFY_CHANNEL не заданы в .env")
        return

    if win < min_win and bet < min_win:
        log.info(f"[notify] ниже порога: win={win} bet={bet} < {min_win}")
        return

    mention = f'<a href="tg://user?id={uid}">@{username or "player"}</a>'
    label = _label(choice)

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
        msg = await bot.send_message(int(source_id), text, parse_mode="HTML")
        log.info(f"[notify] отправлено в source, id={msg.message_id}")

        await bot.forward_message(
            chat_id=int(target_id),
            from_chat_id=int(source_id),
            message_id=msg.message_id
        )
        log.info(f"[notify] переслано в target")

        try:
            await bot.delete_message(int(source_id), msg.message_id)
        except Exception:
            pass

    except Exception as e:
        log.error(f"[notify_result] ОШИБКА: {e}")


async def notify_win(bot, uid, username, game, bet, win, mult, balance=None):
    await notify_result(bot, uid, username, game, "", bet, win, mult,
                        balance or 0.0, True)


async def notify_big_bet(bot, uid, username, game, bet):
    pass