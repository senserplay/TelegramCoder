import asyncio

from aiogram import Bot, Dispatcher
from src.core.config import env_settings
from src.handlers.admin import router as admin_router
from src.handlers.code import router as code_router
from src.handlers.polls import router as polls_router
from src.handlers.start import router as start_router


async def main():
    bot = Bot(env_settings.BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(code_router)
    dp.include_router(admin_router)
    dp.include_router(polls_router)

    print("Bot Started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
