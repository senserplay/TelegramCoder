from logging import Logger

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from dishka import FromDishka
from src.external.llm import prompt
from src.external.llm.proxy_api import ProxyAPI
from src.services.poll import PollService


router = Router()


@router.message(Command("start"))
async def cmd_start(
    message: Message,
    logger: FromDishka[Logger],
    llm: FromDishka[ProxyAPI],
    poll_service: FromDishka[PollService],
):
    logger.info(f"Пользователь {message.from_user.id} запустил бота")

    await poll_service.clear_chat(message)

    await message.answer("Привет! Давайте напишем новую программу, для начала выберем тему")
    themes = llm.send_message(prompt.START_PROMPT)
    if not isinstance(themes, list) or len(themes) < 2:
        await message.answer("Произошла ошибка при генерации тем")
        return

    try:
        question = "Выберите тему программы:"
        poll_message = await message.bot.send_poll(
            chat_id=message.chat.id,
            question=question,
            options=themes[:10],
            is_anonymous=False,
            type="regular",
            allows_multiple_answers=False,
        )
        logger.info(f"Опрос отправлен в чат {message.chat.id}, poll_id={poll_message.poll.id}")

        await poll_service.registration(poll_message)

    except Exception as e:
        logger.error(f"Ошибка отправки опроса: {e}")
        await message.answer("⚠️ Не удалось отправить опрос.")
