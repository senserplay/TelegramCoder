import asyncio

from aiogram import Bot, Dispatcher
from dishka import make_async_container
from dishka.integrations.aiogram import (
    AiogramProvider,
    setup_dishka,
)
from src.core.config import Settings
from src.core.log import logger
from src.core.modules.cache import CacheProvider
from src.core.modules.chat import ChatProvider
from src.core.modules.code import CodeProvider
from src.core.modules.config import ConfigProvider
from src.core.modules.db import DBProvider
from src.core.modules.llm import LLMProvider
from src.core.modules.logger import LoggerProvider
from src.core.modules.poll import PollProvider
from src.handlers.setup import setup_dp
from src.infrastructure.postgres.connection import DATABASE_URL
from src.infrastructure.redis.connection import async_redis_client
from src.worker.poll import setup_poll_worker


config = Settings()
bot = Bot(config.BOT_TOKEN)
dp = Dispatcher()
poll_worker = setup_poll_worker(config, logger, bot, check_interval=10)
container = make_async_container(
    DBProvider(DATABASE_URL),
    CacheProvider(),
    LoggerProvider(),
    ChatProvider(),
    ConfigProvider(),
    LLMProvider(),
    PollProvider(poll_worker),
    CodeProvider(),
    AiogramProvider(),
)

setup_dishka(container, dp, auto_inject=True)
setup_dp(dp)


async def main():
    await poll_worker.start()
    logger.info("🚀 Poll worker успешно запущен")

    try:
        await dp.start_polling(bot)
    finally:
        await poll_worker.stop()
        await async_redis_client.aclose()
        logger.info("🔌 Соединение с Redis закрыто")


if __name__ == "__main__":
    asyncio.run(main())
