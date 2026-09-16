import re
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message


TG_EMOJI_RE = re.compile(r'</?tg-emoji[^>]*>', re.IGNORECASE)


def strip_tg_emoji(text: str) -> str:
    """Убирает теги <tg-emoji ...> и </tg-emoji>, оставляя fallback-эмодзи."""
    return TG_EMOJI_RE.sub("", text)


async def safe_answer(message: Message, text: str, **kwargs):
    """
    Отправляет сообщение. Если Telegram ругается ENTITY_TEXT_INVALID
    (невалидный custom emoji ID) — отправляет без кастомных эмодзи.
    """
    try:
        return await message.answer(text, **kwargs)
    except TelegramBadRequest as e:
        if "ENTITY_TEXT_INVALID" in str(e):
            clean = strip_tg_emoji(text)
            return await message.answer(clean, **kwargs)
        raise


async def safe_edit(message: Message, text: str, **kwargs):
    """
    Редактирует сообщение. Защита от:
      - ENTITY_TEXT_INVALID (невалидный custom emoji ID)
      - message is not modified (тот же текст)
    """
    try:
        return await message.edit_text(text, **kwargs)
    except TelegramBadRequest as e:
        err = str(e)
        if "ENTITY_TEXT_INVALID" in err:
            clean = strip_tg_emoji(text)
            try:
                return await message.edit_text(clean, **kwargs)
            except TelegramBadRequest as e2:
                if "message is not modified" in str(e2):
                    return None
                raise
        if "message is not modified" in err:
            return None
        raise


async def safe_send(bot, chat_id: int, text: str, **kwargs):
    """Универсальный safe-send, если нет объекта message."""
    try:
        return await bot.send_message(chat_id, text, **kwargs)
    except TelegramBadRequest as e:
        if "ENTITY_TEXT_INVALID" in str(e):
            clean = strip_tg_emoji(text)
            return await bot.send_message(chat_id, clean, **kwargs)
        raise