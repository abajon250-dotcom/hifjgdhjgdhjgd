import os
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ChatType
from utils.subscription import check_subscription, subscribe_kb, subscribe_text

ADMIN_ID = int(os.getenv("ADMIN_ID", 0))


class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = getattr(event, "from_user", None)
        if not user:
            return await handler(event, data)

        # В группах не проверяем
        if isinstance(event, Message) and event.chat.type in (
            ChatType.GROUP, ChatType.SUPERGROUP
        ):
            return await handler(event, data)

        # Админ пропускается всегда
        if user.id == ADMIN_ID:
            return await handler(event, data)

        # Проверка подписки на 3 канала
        try:
            not_sub = await check_subscription(event.bot, user.id)
        except Exception:
            not_sub = []

        if not_sub:
            if isinstance(event, Message):
                await event.answer(
                    subscribe_text(),
                    reply_markup=subscribe_kb(),
                    parse_mode="HTML"
                )
            elif isinstance(event, CallbackQuery):
                await event.answer("🔒 Подпишись на каналы!", show_alert=True)
                try:
                    await event.message.answer(
                        subscribe_text(),
                        reply_markup=subscribe_kb(),
                        parse_mode="HTML"
                    )
                except Exception:
                    pass
            return

        return await handler(event, data)