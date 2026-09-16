import os
import logging
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

log = logging.getLogger(__name__)


def _get_channels():
    """Читает каналы из env каждый раз (после load_dotenv)."""
    return [
        {"id": os.getenv("CHANNEL_WINS_ID"),
         "link": os.getenv("CHANNEL_WINS_LINK"),
         "name": "🏆 Крупные ставки и выигрыши"},
        {"id": os.getenv("CHANNEL_CHAT_ID"),
         "link": os.getenv("CHANNEL_CHAT_LINK"),
         "name": "💬 Чат для игры"},
        {"id": os.getenv("CHANNEL_NEWS_ID"),
         "link": os.getenv("CHANNEL_NEWS_LINK"),
         "name": "📰 Новости"},
    ]


async def check_subscription(bot, user_id: int) -> list:
    not_subscribed = []
    for ch in _get_channels():
        if not ch["id"] or not ch["link"]:
            log.warning(f"[sub] Пропуск канала {ch['name']}: нет id/link "
                        f"(id={ch['id']}, link={ch['link']})")
            continue
        try:
            member = await bot.get_chat_member(chat_id=int(ch["id"]),
                                                user_id=user_id)
            log.info(f"[sub] {user_id} в {ch['id']}: {member.status}")
            if member.status in ("left", "kicked"):
                not_subscribed.append(ch)
        except Exception as e:
            log.error(f"[sub] ОШИБКА {ch['id']}: {e}")
    return not_subscribed


def subscribe_kb():
    rows = []
    for ch in _get_channels():
        if ch["link"]:
            rows.append([InlineKeyboardButton(
                text=ch["name"], url=ch["link"], style="primary"
            )])
    rows.append([InlineKeyboardButton(
        text="Проверить подписку", callback_data="check_sub", style="success"
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def subscribe_text() -> str:
    return (
        "🔒 <b>Обязательная подписка</b>\n\n"
        "Чтобы пользоваться ботом, подпишись на наши каналы:\n\n"
        "🏆 <b>Крупные ставки и выигрыши</b>\n"
        "💬 <b>Чат для игры</b>\n"
        "📰 <b>Новостной канал</b>\n\n"
        "После подписки нажми «<b>Проверить подписку</b>»."
    )