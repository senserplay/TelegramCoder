from logging import Logger

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, PollAnswer
from dishka import FromDishka
from src.filters.admin import AdminFilter
from src.infrastructure.redis.storages.poll import PollStorage
from src.services.poll import PollService


router = Router()


@router.poll_answer()
async def handle_poll_answer(
    poll_answer: PollAnswer, logger: FromDishka[Logger], poll_storage: FromDishka[PollStorage]
):
    await poll_storage.add_vote(poll_answer.poll_id, poll_answer.user.id, poll_answer.option_ids[0])
    logger.info(
        f"Пользователь {poll_answer.user.id} проголосовал за вариант {poll_answer.option_ids} в опросе {poll_answer.poll_id}"
    )


@router.message(Command("sendnow"), AdminFilter())
async def cmd_start(
    message: Message,
    logger: FromDishka[Logger],
    poll_service: FromDishka[PollService],
):
    logger.info(
        f"Пользователь {message.from_user.id} запросил отправку отпроса в чате {message.chat.id}"
    )
    await poll_service.process_chat_poll(message.chat.id, message.bot)
