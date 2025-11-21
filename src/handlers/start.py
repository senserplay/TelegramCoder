from logging import Logger

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from dishka import FromDishka


router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, logger: FromDishka[Logger]):
    logger.info(f"Пользователь {message.from_user.id} запустил бота")
    await message.answer("Привет! Добро пожаловать в бота!")
