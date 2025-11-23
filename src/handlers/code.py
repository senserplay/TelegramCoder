from logging import Logger
from typing import List

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from dishka import FromDishka
from src.application.schemas.code_line import CodeLineResponseDTO
from src.filters.admin import AdminFilter
from src.services.code_line import CodeLineService


router = Router()


@router.message(Command("code"))
async def cmd_code(
    message: Message,
    logger: FromDishka[Logger],
    code_line_service: FromDishka[CodeLineService],
):
    logger.info(f"Поступил запрос на получение кода по чату {message.chat.id}")

    try:
        code_lines = await code_line_service.get_chat_code(message.chat.id)
        await print_code_lines(message, logger, code_lines)

    except Exception as e:
        logger.error(f"Ошибка получения кода для чата {message.chat.id}: {str(e)}")
        await message.answer(
            "❌ Произошла ошибка при получении кода. Попробуйте позже или обратитесь к администратору.",
            parse_mode=ParseMode.MARKDOWN,
        )


@router.message(Command("code_completed"), AdminFilter())
async def cmd_code_completed(
    message: Message,
    logger: FromDishka[Logger],
    code_line_service: FromDishka[CodeLineService],
):
    logger.info(f"Поступил запрос на рефакторинг кода в чате {message.chat.id}")
    completed_code_lines = await code_line_service.code_complete(message.chat.id)
    await print_code_lines(message, logger, completed_code_lines)


async def print_code_lines(message: Message, logger: Logger, code_lines: List[CodeLineResponseDTO]):
    if not code_lines:
        await message.answer(
            "📋 В этом чате пока нет кода. Начните с команды /start для создания первого опроса!"
        )
        return

    formatted_lines = [f"{i + 1}: {line.content}" for i, line in enumerate(code_lines)]
    code_text = "\n".join(formatted_lines)

    code_text = code_text.replace("`", "\\`").replace("\\", "\\\\")

    await message.answer(
        f"💻 Текущий код чата:\n\n```python\n{code_text}\n```", parse_mode=ParseMode.MARKDOWN
    )
    logger.info(f"Успешно отправлен код для чата {message.chat.id} ({len(code_lines)} строк)")
