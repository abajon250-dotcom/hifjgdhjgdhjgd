import os
import logging
from aiogram import Bot

log = logging.getLogger(__name__)


def _ids():
    return (
        os.getenv("SOURCE_CHANNEL_ID"),
        os.getenv("WIN_NOTIFY_CHANNEL"),
        float(os.getenv("WIN_NOTIFY_MIN", 10)),
    )


CHOICE_TEXT = {
    "even": "чётное", "odd": "нечётное",
    "less": "меньше", "more": "больше",
    "sum7_less": "сумма < 7", "sum7_greater": "сумма > 7", "sum7_exact": "сумма = 7",
    "double": "дубль", "sum_prod": "сумма/произведение",
    "corridor": "коридор", "sniper": "снайпер", "lift": "лифт",
    "triple": "трипл", "big": "большой куб",
    "clean": "чистый гол", "any": "любой гол", "stuck": "застрял",
    "miss": "промах", "center": "центр", "red": "красный",
    "white": "белый", "bounce": "отскок", "nine": "девятка",
    "bar": "штанга", "strike": "страйк",
    "otskok": "отскок", "blizko": "близко", "zastryal": "застрял",
    "edge": "с краем", "direct": "прямое",
    "777": "777", "77x": "77*", "lucky7": "лаки 7", "lines": "линии",
    "sum": "сумма", "piggy": "копилка", "ladder": "лесенка",
    "no_6": "не 6", "numbers": "числа", "no_numbers": "без чисел",
    "ladder1": "лесенка", "ladder2": "лесенка",
}


def _label(choice):
    if choice in CHOICE_TEXT:
        return CHOICE_TEXT[choice]
    if choice.startswith("num"):
        return f"на число {choice[3:]}"
    if choice.startswith("exact_"):
        return f"на точное {choice.split('_')[1]}"
    if choice.startswith("two"):
        return f"на {choice[3:]}"
    return choice


async def _send_to_channels(bot: Bot, text: str):
    source, target, _ = _ids()
    if not source or not target:
        log.warning("[notify] каналы не заданы")
        return None
    try:
        msg = await bot.send_message(int(source), text, parse_mode="HTML")
        await bot.forward_message(chat_id=int(target),
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
#              ПУСТЫШКА — кубики НЕ пересылаем
# ============================================================
async def notify_dice(bot: Bot, uid: int, dice_msg):
    """Ничего не делает. Кубики в канал не идут."""
    return


# ============================================================
#              ДЕПОЗИТ
# ============================================================
async def notify_deposit(bot, uid, username, amount):
    source, target, min_dep = _ids()
    if not source or not target:
        return
    if amount < min_dep:
        return
    mention = f'<a href="tg://user?id={uid}">{username or "player"}</a>'
    text = (f'<tg-emoji emoji-id="5445355530111437729">📤</tg-emoji> '
            f'<b>Депозит</b>\n\n'
            f'👤 {mention}\n'
            f'💰 Сумма: <b>{amount:.2f}</b> USDT')
    await _send_to_channels(bot, text)


# ============================================================
#              ВЫВОД
# ============================================================
async def notify_withdraw(bot, uid, username, amount, method):
    source, target, min_dep = _ids()
    if not source or not target:
        return
    if amount < min_dep:
        return
    mention = f'<a href="tg://user?id={uid}">{username or "player"}</a>'
    text = (f'<tg-emoji emoji-id="5443127283898405358">📥</tg-emoji> '
            f'<b>Вывод</b>\n\n'
            f'👤 {mention}\n'
            f'💰 Сумма: <b>{amount:.2f}</b> USDT\n'
            f'🏦 Способ: <b>{method}</b>')
    await _send_to_channels(bot, text)


# ============================================================
#              КРУПНАЯ СТАВКА (>= WIN_NOTIFY_MIN)
# ============================================================
async def notify_bet(bot, uid, username, game_name, bet, emoji="🎲"):
    source, target, min_bet = _ids()
    if not source or not target:
        return
    if bet < min_bet:
        return
    mention = f'<a href="tg://user?id={uid}">{username or "player"}</a>'
    text = (f'<tg-emoji emoji-id="5321230889357713132">🎲</tg-emoji> '
            f'<b>{mention}</b>, ставка — <b>{bet:.2f}</b>💲\n\n'
            f'🎮 Игра: <b>{game_name}</b>')
    await _send_to_channels(bot, text)


# ============================================================
#              КРУПНЫЙ ВЫИГРЫШ (>= WIN_NOTIFY_MIN)
# ============================================================
async def notify_result(bot, uid, username, game_name, choice,
                        bet, win, mult, balance, is_win):
    source, target, min_win = _ids()
    if not source or not target:
        return
    # идёт в канал, если ставка ИЛИ выигрыш >= минимума
    if bet < min_win and win < min_win:
        return

    mention = f'<a href="tg://user?id={uid}">{username or "player"}</a>'
    label = _label(choice)

    if is_win:
        header = (f'<tg-emoji emoji-id="5449683594425410231">🔼</tg-emoji> '
                  f'<b>{mention}</b>, выиграл <b>{win:.2f}</b>💲')
    else:
        header = (f'<tg-emoji emoji-id="5447183459602669338">🔽</tg-emoji> '
                  f'<b>{mention}</b>, проиграл <b>{bet:.2f}</b>💲')

    text = (f"{header}\n\n"
            f"<blockquote>"
            f'<tg-emoji emoji-id="5321230889357713132">🎲</tg-emoji> '
            f"{game_name} — {label} × {mult:.2f}"
            f"</blockquote>\n\n"
            f"Ставка: <b>{bet:.2f}</b>💲\n"
            f"Баланс: <b>{balance:.2f}</b>")
    await _send_to_channels(bot, text)