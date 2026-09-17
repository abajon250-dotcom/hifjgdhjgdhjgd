import os
import logging
from aiogram import Bot

log = logging.getLogger(__name__)


def _ids():
    return (os.getenv("SOURCE_CHANNEL_ID"),
            os.getenv("WIN_NOTIFY_CHANNEL"),
            float(os.getenv("WIN_NOTIFY_MIN", 10)))


# Русские названия игр (для вывода в канал)
GAME_RU = {
    "football": "Футбол", "basketball": "Баскет",
    "darts": "Дартс", "bowling": "Боулинг",
    "Куб": "Куб", "Слоты": "Слоты",
}


# Русские названия исходов
CHOICE_TEXT = {
    # футбол
    "mimo": "мимо ворот", "shtanga": "в штангу",
    "center": "в центр", "from_shtanga": "от штанги",
    "corner": "в угол",
    # баскет
    "otskok": "отскок", "blizko": "близко",
    "zastryal": "застрял", "edge": "с краем", "direct": "прямое",
    # дартс
    "miss": "промах", "bull": "в центр",
    "s1": "сектор 1", "s2": "сектор 2", "s3": "сектор 3", "s4": "сектор 4",
    # боулинг
    "p1": "1/6", "p3": "3/6", "p4": "4/6", "p5": "5/6", "strike": "страйк",
    # кубики
    "even": "чёт", "odd": "нечёт",
    "less": "меньше", "more": "больше",
    "double": "дубль", "triple": "трипл",
    "no_6": "не 6", "big": "большой куб",
    "sum7_exact": "сумма 7", "sum7_less": "сумма <7", "sum7_greater": "сумма >7",
    "corridor": "коридор", "sniper": "снайпер", "lift": "лифт",
    "sum_prod": "сумма/произв", "numbers": "числа", "no_numbers": "без чисел",
    "ladder1": "лесенка", "ladder2": "лесенка",
    # слоты
    "any": "любая комбинация", "unique": "уникальные", "combo": "7+BAR",
    "one": "одна 7", "exact": "3×7",
    # аркады
    "crash": "краш", "keno": "кено", "roulette": "рулетка",
}


def _label(choice):
    if choice in CHOICE_TEXT:
        return CHOICE_TEXT[choice]
    if choice.startswith("num"):
        return f"число {choice[3:]}"
    if choice.startswith("two"):
        return f"на {choice[3:]}"
    return choice


async def _send_to_channels(bot: Bot, text: str):
    source, target, _ = _ids()
    if not source or not target:
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


async def notify_dice(bot, uid, dice_msg):
    return


async def notify_deposit(bot, uid, username, amount):
    source, target, min_dep = _ids()
    if not source or not target or amount < min_dep: return
    mention = f'<a href="tg://user?id={uid}">{username or "player"}</a>'
    text = (f'📤 <b>Депозит</b>\n\n👤 {mention}\n'
            f'💰 Сумма: <b>{amount:.2f}</b> USDT')
    await _send_to_channels(bot, text)


async def notify_withdraw(bot, uid, username, amount, method):
    source, target, min_dep = _ids()
    if not source or not target or amount < min_dep: return
    mention = f'<a href="tg://user?id={uid}">{username or "player"}</a>'
    text = (f'📥 <b>Вывод</b>\n\n👤 {mention}\n'
            f'💰 Сумма: <b>{amount:.2f}</b> USDT\n🏦 Способ: <b>{method}</b>')
    await _send_to_channels(bot, text)


async def notify_bet(bot, uid, username, game_name, bet, emoji="🎲"):
    source, target, min_bet = _ids()
    if not source or not target or bet < min_bet: return
    mention = f'<a href="tg://user?id={uid}">{username or "player"}</a>'
    text = (f'🎲 <b>{mention}</b>, ставка — <b>{bet:.2f}</b>💲\n\n'
            f'🎮 Игра: <b>{game_name}</b>')
    await _send_to_channels(bot, text)


async def notify_result(bot, uid, username, game_name, choice,
                        bet, win, mult, balance, is_win):
    source, target, min_win = _ids()
    if not source or not target or (bet < min_win and win < min_win):
        return

    mention = f'<a href="tg://user?id={uid}">{username or "player"}</a>'
    label = _label(choice)
    # человеческое название игры
    game_ru = GAME_RU.get(game_name, game_name)

    if is_win:
        header = f'🔼 <b>{mention}</b>, выиграл <b>{win:.2f}</b>💲'
    else:
        header = f'🔽 <b>{mention}</b>, проиграл <b>{bet:.2f}</b>💲'

    text = (f"{header}\n\n"
            f"<blockquote>🎲 {game_ru} — {label} × {mult:.2f}</blockquote>\n\n"
            f"Ставка: <b>{bet:.2f}</b>💲\n"
            f"Баланс: <b>{balance:.2f}</b>")
    await _send_to_channels(bot, text)