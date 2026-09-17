import os
import logging
from aiogram import Bot

log = logging.getLogger(__name__)


def _ids():
    return (
        os.getenv("SOURCE_CHANNEL_ID"),
        os.getenv("WIN_NOTIFY_CHANNEL"),
        float(os.getenv("WIN_NOTIFY_MIN", 1)),
    )


CHOICE_TEXT = {
    "even": "чётное", "odd": "нечётное",
    "less": "меньше", "more": "больше",
    "sum7_less": "сумма < 7", "sum7_greater": "сумма > 7",
    "sum7_exact": "сумма = 7",
    "double": "дубль", "sum_prod": "сумма/произведение",
    "corridor": "коридор", "sniper": "снайпер", "lift": "лифт",
    "three_even": "три чёт", "three_odd": "три нечет",
    "triple": "трипл", "unique": "уникальные",
    "straight": "стрит", "combination": "комбо",
    "greater_10": "сумма > 10", "less_11": "сумма < 11",
    "big": "большой куб",
    "clean": "чистый гол", "any": "любой гол", "stuck": "застрял",
    "miss": "промах", "center": "центр", "red": "красный",
    "white": "белый", "bounce": "отскок", "nine": "девятка",
    "bar": "штанга", "strike": "страйк",
    "otskok": "отскок", "blizko": "близко", "zastryal": "застрял",
    "edge": "с краем", "direct": "прямое",
    "777": "777", "77x": "77*", "any_sl": "любая комбинация",
    "lucky7": "лаки 7", "lines": "линии", "sum": "сумма",
    "piggy": "копилка", "ladder": "лесенка",
    "no_6": "не 6",
    "numbers": "числа", "no_numbers": "без чисел",
    "ladder1": "лесенка", "ladder2": "лесенка",
}


def _label(choice):
    if choice in CHOICE_TEXT:
        return CHOICE_TEXT[choice]
    if choice.startswith("num"):
        return f"на число {choice[3:]}"
    if choice.startswith("exact_"):
        return f"на точное {choice.split('_')[1]}"
    if choice.startswith("prod_"):
        return f"произв. ≥ {choice.split('_')[1]}"
    if choice.startswith("two"):
        return f"на {choice[3:]}"
    return choice


async def _send_to_channels(bot: Bot, text: str, parse_mode="HTML"):
    """Пишет в SOURCE и пересылает в TARGET."""
    source, target, _ = _ids()
    if not source or not target:
        log.warning("[notify] каналы не заданы")
        return None
    try:
        msg = await bot.send_message(int(source), text, parse_mode=parse_mode)
        await bot.forward_message(
            chat_id=int(target),
            from_chat_id=int(source),
            message_id=msg.message_id)
        try:
            await bot.delete_message(int(source), msg.message_id)
        except Exception:
            pass
        return msg
    except Exception as e:
        log.error(f"[notify] {e}")
        return None


# ============================================================
#              ПЕРЕСЫЛ КУБА В КАНАЛ
# ============================================================
async def notify_dice(bot: Bot, uid: int, dice_msg):
    """
    Форвардит сообщение с кубом из ЛС игрока в SOURCE,
    потом копирует в TARGET, потом удаляет из SOURCE.
    Работает только для сообщений с кубиками (answer_dice).
    """
    source, target, _ = _ids()
    if not source or not target:
        return
    if dice_msg is None:
        return
    try:
        # 1. Форвард куба из ЛС игрока в SOURCE
        fwd = await bot.forward_message(
            chat_id=int(source),
            from_chat_id=uid,
            message_id=dice_msg.message_id)
        # 2. Форвард из SOURCE в TARGET
        await bot.forward_message(
            chat_id=int(target),
            from_chat_id=int(source),
            message_id=fwd.message_id)
        # 3. Удаляем из SOURCE
        try:
            await bot.delete_message(int(source), fwd.message_id)
        except Exception:
            pass
    except Exception as e:
        log.error(f"[notify_dice] {e}")


# ============================================================
#              УВЕДОМЛЕНИЕ О ДЕПОЗИТЕ
# ============================================================
async def notify_deposit(bot, uid, username, amount):
    source, target, min_dep = _ids()
    if not source or not target:
        return
    if amount < min_dep:
        return
    mention = f'<a href="tg://user?id={uid}">{username or "player"}</a>'
    text = (
        f'<tg-emoji emoji-id="5445355530111437729">📤</tg-emoji> '
        f'<b>Депозит</b>\n\n'
        f'👤 {mention}\n'
        f'💰 Сумма: <b>{amount:.2f}</b> USDT'
    )
    await _send_to_channels(bot, text)


# ============================================================
#              СТАВКА
# ============================================================
async def notify_bet(bot, uid, username, game_name, bet, emoji="🎲"):
    source, target, min_bet = _ids()
    if not source or not target:
        return
    if bet < min_bet:
        return
    mention = f'<a href="tg://user?id={uid}">{username or "player"}</a>'
    text = (
        f'<tg-emoji emoji-id="5321230889357713132">🎲</tg-emoji> '
        f'<b>{mention}</b>, ставка — <b>{bet:.2f}</b>💲'
    )
    await _send_to_channels(bot, text)


# ============================================================
#              РЕЗУЛЬТАТ ИГРЫ
# ============================================================
async def notify_result(bot, uid, username, game_name, choice,
                        bet, win, mult, balance, is_win):
    source, target, min_win = _ids()
    if not source or not target:
        return
    if win < min_win and bet < min_win:
        return

    mention = f'<a href="tg://user?id={uid}">{username or "player"}</a>'
    label = _label(choice)

    if is_win:
        header = (
            f'<tg-emoji emoji-id="5449683594425410231">🔼</tg-emoji> '
            f'<b>{mention}</b>, выиграл <b>{win:.2f}</b>💲'
        )
    else:
        header = (
            f'<tg-emoji emoji-id="5447183459602669338">🔽</tg-emoji> '
            f'<b>{mention}</b>, проиграл <b>{bet:.2f}</b>💲'
        )

    text = (
        f"{header}\n\n"
        f"<blockquote>"
        f'<tg-emoji emoji-id="5321230889357713132">🎲</tg-emoji> '
        f"{game_name} — {label} × {mult:.2f}"
        f"</blockquote>\n\n"
        f"Ставка: <b>{bet:.2f}</b>💲\n"
        f"Баланс: <b>{balance:.2f}</b>"
    )
    await _send_to_channels(bot, text)