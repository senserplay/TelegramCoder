import asyncio

from aiogram import Bot, Dispatcher
from dishka import make_async_container
from dishka.integrations.aiogram import (
    AiogramProvider,
    setup_dishka,
)
from src.core.config import env_settings
from src.core.modules.cache import CacheProvider
from src.core.modules.chat import ChatProvider
from src.core.modules.config import ConfigProvider
from src.core.modules.db import DBProvider
from src.core.modules.llm import LLMProvider
from src.core.modules.logger import LoggerProvider
from src.handlers.setup import setup_dp
from src.infrastructure.postgres.connection import DATABASE_URL


async def main():
    bot = Bot(env_settings.BOT_TOKEN)
    dp = Dispatcher()
    container = make_async_container(
        DBProvider(DATABASE_URL),
        CacheProvider(),
        LoggerProvider(),
        ChatProvider(),
        ConfigProvider(),
        LLMProvider(),
        AiogramProvider(),
    )

    setup_dishka(container, dp, auto_inject=True)
    setup_dp(dp)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
