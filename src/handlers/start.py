from logging import Logger

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from dishka import FromDishka
from src.filters.admin import AdminFilter
from src.filters.private_chat import PrivateChatFilter
from src.services.chat import ChatService
from src.services.code_line import CodeLineService
from src.services.poll import PollService


router = Router()


@router.message(Command("start"), AdminFilter())
async def cmd_start(
    message: Message,
    logger: FromDishka[Logger],
    poll_service: FromDishka[PollService],
    code_line_service: FromDishka[CodeLineService],
):
    logger.info(f"Пользователь {message.from_user.id} запустил бота")
    await code_line_service.clear_chat_code(message.chat.id)
    await poll_service.clear_chat(message)
    await message.answer("Привет! Давайте напишем новую программу")
    await poll_service.create_poll_for_chat(message.chat.id, message.bot)


@router.message(Command("start"), PrivateChatFilter())
async def cmd_start_private(
    message: Message,
    logger: FromDishka[Logger],
    poll_service: FromDishka[PollService],
    code_line_service: FromDishka[CodeLineService],
    chat_service: FromDishka[ChatService],
):
    await chat_service.registration(message.chat)
    logger.info(f"Пользователь {message.from_user.id} запустил бота")
    await code_line_service.clear_chat_code(message.chat.id)
    await poll_service.clear_chat(message)
    await message.answer("Привет! Давайте напишем новую программу")
    await poll_service.create_poll_for_chat(message.chat.id, message.bot)
