from aiogram import Dispatcher
from src.handlers.admin import router as admin_router
from src.handlers.code import router as code_router
from src.handlers.group import router as group_router
from src.handlers.polls import router as polls_router
from src.handlers.start import router as start_router


def setup_dp(dp: Dispatcher):
    dp.include_router(start_router)
    dp.include_router(code_router)
    dp.include_router(admin_router)
    dp.include_router(polls_router)
    dp.include_router(group_router)
