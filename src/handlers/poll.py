from logging import Logger

from aiogram import Router
from aiogram.types import PollAnswer
from dishka import FromDishka
from src.infrastructure.redis.storages.poll import PollStorage


router = Router()


# sendnow (админ): отправить следующий опрос немедленно
@router.poll_answer()
async def handle_poll_answer(
    poll_answer: PollAnswer, logger: FromDishka[Logger], poll_storage: FromDishka[PollStorage]
):
    logger.info(f"{poll_answer.option_ids}")
    await poll_storage.add_vote(poll_answer.poll_id, poll_answer.user.id, poll_answer.option_ids[0])
    logger.info(
        f"Пользователь {poll_answer.user.id} проголосовал за вариант {poll_answer.option_ids} в опросе {poll_answer.poll_id}"
    )
