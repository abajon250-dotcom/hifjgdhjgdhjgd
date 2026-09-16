import asyncio
import logging
import os
import re
from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message as TgMessage

# ============================================================
#        ХАК: edit_text не падает на ошибки Telegram
# ============================================================
_orig_edit = TgMessage.edit_text


async def _safe_edit(self, text=None, *args, **kwargs):
    try:
        return await _orig_edit(self, text, *args, **kwargs)
    except TelegramBadRequest as e:
        err = str(e)
        if "message is not modified" in err:
            return None
        if "ENTITY_TEXT_INVALID" in err and isinstance(text, str):
            clean = re.sub(r'</?tg-emoji[^>]*>', '', text)
            try:
                return await _orig_edit(self, clean, *args, **kwargs)
            except TelegramBadRequest:
                return None
        raise


TgMessage.edit_text = _safe_edit
# ============================================================

from handlers.start import router as start_router
from handlers.text_commands import router as text_router
from handlers.games_menu import router as games_router
from handlers.payments import router as payments_router
from handlers.wallet import router as wallet_router
from handlers.dice_games import router as dice_router
from handlers.sport_games import router as sport_router
from handlers.slots import router as slots_router
from handlers.arcades import router as arcades_router
from handlers.admin import router as admin_router
from middlewares.subscription import SubscriptionMiddleware

TOKEN = os.getenv("BOT_TOKEN")


async def set_bot_commands(bot: Bot):
    from aiogram.types import BotCommand
    await bot.set_my_commands([
        BotCommand(command="start",   description="🚀 Запустить бота"),
        BotCommand(command="menu",    description="📋 Главное меню"),
        BotCommand(command="balance", description="💵 Мой баланс"),
        BotCommand(command="games",   description="🎮 Меню игр"),
        BotCommand(command="top",     description="🏆 Топ игроков"),
        BotCommand(command="help",    description="❓ Помощь"),
    ])


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    if not TOKEN:
        print("❌ BOT_TOKEN не найден в .env!")
        return

    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Только подписка в ЛС
    sub_mw = SubscriptionMiddleware()
    dp.message.middleware(sub_mw)
    dp.callback_query.middleware(sub_mw)

    # ⚠️ group_router и group_filter УБРАНЫ — всё работает через text_commands
    dp.include_router(start_router)
    dp.include_router(text_router)
    dp.include_router(games_router)
    dp.include_router(payments_router)
    dp.include_router(wallet_router)
    dp.include_router(dice_router)
    dp.include_router(sport_router)
    dp.include_router(slots_router)
    dp.include_router(arcades_router)
    dp.include_router(admin_router)

    await bot.delete_webhook(drop_pending_updates=True)
    await set_bot_commands(bot)

    me = await bot.get_me()
    print(f"✅ Бот @{me.username} запущен!")
    print(f"👑 Админ ID: {os.getenv('ADMIN_ID')}")
    print(f"🎰 Казино: {os.getenv('CASINO_NAME', 'Onyx')}")

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 Бот остановлен.")