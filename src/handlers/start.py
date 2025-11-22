from logging import Logger

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from dishka import FromDishka
from src.external.llm import prompt
from src.external.llm.proxy_api import ProxyAPI


router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, logger: FromDishka[Logger], llm: FromDishka[ProxyAPI]):
    logger.info(f"Пользователь {message.from_user.id} запустил бота")

    themes = llm.send_message(prompt.START_PROMPT)
    if not isinstance(themes, list) or len(themes) < 2:
        themes = ["Тема 1", "Тема 2", "Тема 3"]  # fallback

    await message.answer(f"Привет! Добро пожаловать в бота! Вот ваши темы: {', '.join(themes)}")

    try:
        poll_message = await message.bot.send_poll(
            chat_id=message.chat.id,
            question="Выберите тему для обсуждения:",
            options=themes[:10],
            is_anonymous=False,
            type="regular",
            allows_multiple_answers=False,
        )
        logger.info(f"Опрос отправлен в чат {message.chat.id}, poll_id={poll_message.poll.id}")
    except Exception as e:
        logger.error(f"Ошибка отправки опроса: {e}")
        await message.answer("⚠️ Не удалось отправить опрос.")
