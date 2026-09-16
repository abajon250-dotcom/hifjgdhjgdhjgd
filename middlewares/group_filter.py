from aiogram import BaseMiddleware
from aiogram.types import Message
from aiogram.enums import ChatType

# Команды, разрешённые в группах
ALLOWED = {
    "balance", "bal", "top", "stats", "help",
    "баланс", "бал", "топ", "стата", "профиль", "статистика", "помощь", "хелп",
    "dice", "куб", "кубик", "дайс", "слоты", "slots",
}


class GroupFilterMiddleware(BaseMiddleware):
    """В группах разрешает только команды из белого списка."""
    async def __call__(self, handler, event, data):
        if isinstance(event, Message) and event.chat.type in (
            ChatType.GROUP, ChatType.SUPERGROUP
        ):
            text = (event.text or "").strip()
            if text.startswith("/"):
                cmd = text.split()[0][1:].split("@")[0].lower()
                if cmd not in ALLOWED:
                    return  # молча игнорируем
            elif text:
                # Просто текст в группе — игнорируем
                return
        return await handler(event, data)