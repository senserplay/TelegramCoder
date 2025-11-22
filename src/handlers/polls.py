from logging import Logger

from aiogram import Router
from aiogram.types import PollAnswer
from dishka import FromDishka


router = Router()


# sendnow (админ): отправить следующий опрос немедленно
@router.poll_answer()
async def handle_poll_answer(poll_answer: PollAnswer, logger: FromDishka[Logger]):
    logger.info(
        f"Пользователь {poll_answer.user.id} проголосовал за вариант {poll_answer.option_ids} в опросе {poll_answer.poll_id}"
    )
