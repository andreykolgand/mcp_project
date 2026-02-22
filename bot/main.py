"""Точка входа: запуск бота и подключение к БД."""
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import BOT_TOKEN
from bot.logging_config import setup_logging, consume_log_queue, stop_log_queue
from bot.database import init_db, close_pool
from bot.handlers import messages_router, stats_router, top_router

logger = logging.getLogger(__name__)

async def main() -> None:
    setup_logging()
    logger.info("Запуск бота...")
    try:
        await init_db()
    except Exception as e:
        logger.exception("Не удалось инициализировать БД: %s", e)
        sys.exit(1)
    log_consumer = asyncio.create_task(consume_log_queue())
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(stats_router)
    dp.include_router(top_router)
    dp.include_router(messages_router)
    try:
        logger.info("Бот запущен, ожидание обновлений")
        await dp.start_polling(bot)
    finally:
        stop_log_queue()
        await log_consumer
        await close_pool()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
