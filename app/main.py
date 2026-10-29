import asyncio
import logging
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.database.session import init_db
from app.scheduler.scheduler import setup_scheduler
from app.bot.middlewares.subscription import ChannelSubscriptionMiddleware

# Handlerlar
from app.bot.handlers import (
    start,
    prayers,
    reminders,
    journal,
    qaza,
    reports,
    settings as bot_settings_handler,
    ehson,
    admin
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("namoz-sarhisobi")

async def main():
    logger.info("Bot tizimi ishga tushirilmoqda...")

    if not settings.BOT_TOKEN:
        logger.error("BOT_TOKEN aniqlanmadi! Iltimos, .env faylida BOT_TOKEN ni ko'rsating.")
        return

    # Ma'lumotlar bazasini initsializatsiya qilish
    logger.info("Ma'lumotlar bazasi jadvallari tekshirilmoqda...")
    await init_db()
    logger.info("Ma'lumotlar bazasi tayyor.")

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Middleware
    dp.message.outer_middleware(ChannelSubscriptionMiddleware())
    dp.callback_query.outer_middleware(ChannelSubscriptionMiddleware())

    # Routerlarni ulash
    dp.include_router(start.router)
    dp.include_router(prayers.router)
    dp.include_router(reminders.router)
    dp.include_router(journal.router)
    dp.include_router(qaza.router)
    dp.include_router(reports.router)
    dp.include_router(bot_settings_handler.router)
    dp.include_router(ehson.router)
    dp.include_router(admin.router)

    # Scheduler ni ishga tushirish
    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("Scheduler muvaffaqiyatli ishga tushirildi.")

    try:
        logger.info("Bot polling rejimi boshlandi...")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()
        logger.info("Bot to'xtatildi.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot qo'lda to'xtatildi.")
