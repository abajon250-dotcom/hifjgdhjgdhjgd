import os
import logging
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ChatType
from utils.subscription import check_subscription, subscribe_kb, subscribe_text

log = logging.getLogger(__name__)
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))


class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = getattr(event, "from_user", None)
        if not user:
            log.warning("[mw] Нет user, пропускаю")
            return await handler(event, data)

        # В группах не проверяем
        if isinstance(event, Message) and event.chat.type in (
            ChatType.GROUP, ChatType.SUPERGROUP
        ):
            log.info(f"[mw] группа, пропускаю {user.id}")
            return await handler(event, data)

        # Админ пропускается
        if user.id == ADMIN_ID:
            log.info(f"[mw] админ {user.id}, пропускаю")
            return await handler(event, data)

        try:
            not_sub = await check_subscription(event.bot, user.id)
            log.info(f"[mw] {user.id} не подписан на {len(not_sub)} каналов")
        except Exception as e:
            log.error(f"[mw] ошибка проверки: {e}")
            not_sub = []

        if not_sub:
            log.info(f"[mw] БЛОКИРУЮ {user.id}")
            if isinstance(event, Message):
                await event.answer(subscribe_text(),
                                   reply_markup=subscribe_kb(),
                                   parse_mode="HTML")
            elif isinstance(event, CallbackQuery):
                await event.answer("🔒 Подпишись!", show_alert=True)
            return

        log.info(f"[mw] пропускаю {user.id}")
        return await handler(event, data)