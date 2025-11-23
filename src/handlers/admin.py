import asyncio
import html
import time
from logging import Logger
from typing import List

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import FSInputFile, Message
from dishka import FromDishka
from src.core.log import get_log_file_path, read_full_log, read_last_n_lines
from src.filters.admin import AdminFilter
from src.infrastructure.redis.storages.poll import PollStorage
from src.worker.poll import PollWorker


START_TIME = time.time()

router = Router()


@router.message(Command("health"), AdminFilter())
async def cmd_health(
    message: Message,
    poll_storage: FromDishka[PollStorage],
    poll_worker: FromDishka[PollWorker],
    logger: FromDishka[Logger],
):
    logger.info(f"Админ {message.from_user.id} запросил статус здоровья")

    uptime_seconds = int(time.time() - START_TIME)
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"

    active_polls = await poll_storage.get_all_active_polls()
    active_count = len(active_polls)

    worker_status = await poll_worker.get_status()
    if worker_status["status"] == "running":
        if worker_status["last_check_ago"] is not None:
            worker_str = (
                f"✅ Работает (последняя проверка: {worker_status['last_check_ago']} сек назад)"
            )
        else:
            worker_str = "✅ Работает (ещё не проверял опросы)"
    else:
        worker_str = "❌ Остановлен"

    response = (
        "🩺 <b>Состояние системы</b>:\n\n"
        f"⏱ <b>Uptime:</b> {uptime_str}\n"
        f"🤖 <b>Poll Worker:</b> {worker_str}\n"
        f"📊 <b>Активных опросов:</b> {active_count}\n"
    )

    await message.answer(response, parse_mode="HTML")


@router.message(Command("logs"), AdminFilter())
async def cmd_logs(message: Message, logger: FromDishka[Logger]):
    logger.info(f"Админ {message.from_user.id} запросил последние логи")
    log_path = get_log_file_path()
    loop = asyncio.get_running_loop()
    raw_lines = await loop.run_in_executor(None, read_last_n_lines, log_path, 100)

    escaped_lines = [html.escape(line) for line in raw_lines]
    log_content = "\n".join(escaped_lines)
    full_text = "📜 <b>Последние 100 строк лога:</b>\n\n" "<code>" + log_content + "</code>"

    if len(full_text) <= 4096:
        await message.answer(full_text, parse_mode="HTML")
    else:
        content_parts = split_text_for_html(log_content, max_length=3900)
        for i, part in enumerate(content_parts, 1):
            chunk = f"📜 <b>Лог (часть {i}/{len(content_parts)})</b>\n\n" f"<code>{part}</code>"
            try:
                await message.answer(chunk, parse_mode="HTML")
            except Exception as e:
                logger.exception(f"Ошибка отправки части {i}")
                await message.answer(f"⚠️ Ошибка в части {i}: {e}")
                break


@router.message(Command("alllogs"), AdminFilter())
async def cmd_alllogs(message: Message, logger: FromDishka[Logger]):
    logger.info(f"Админ {message.from_user.id} запросил полный лог")

    log_path = get_log_file_path()

    if not log_path.exists():
        await message.answer("❌ Лог-файл не найден.")
        return

    file_size = log_path.stat().st_size
    MAX_TELEGRAM_FILE_SIZE = 50 * 1024 * 1024

    if file_size > MAX_TELEGRAM_FILE_SIZE:
        loop = asyncio.get_running_loop()
        content = await loop.run_in_executor(None, read_full_log, log_path)
        text = (
            "📎 <b>Полный лог (слишком большой для файла, отправляю текстом):</b>\n\n<code>"
            + content[:9000].replace("<", "<").replace(">", ">")
            + ("..." if len(content) > 9000 else "")
            + "</code>"
        )
        parts = split_text(text, max_length=4000)
        for part in parts[:5]:
            await message.answer(part, parse_mode="HTML")
        if len(parts) > 5:
            await message.answer("⚠️ Лог слишком длинный — показаны только первые ~45k символов.")
    else:
        try:
            await message.answer_document(
                FSInputFile(log_path, filename="bot.log"),
                caption=f"📁 Полный лог-файл ({file_size / 1024:.1f} КБ)",
            )
        except Exception as e:
            await message.answer(f"❌ Не удалось отправить файл: {e}")


def split_text(text: str, max_length: int = 4000) -> List[str]:
    if len(text) <= max_length:
        return [text]
    lines = text.splitlines(keepends=True)
    parts = []
    current = ""
    for line in lines:
        if len(current) + len(line) > max_length:
            parts.append(current)
            current = line
        else:
            current += line
    if current:
        parts.append(current)
    return parts


def split_text_for_html(text: str, max_length: int = 4000) -> List[str]:
    if len(text) <= max_length:
        return [text]

    parts = []
    while text:
        if len(text) <= max_length:
            parts.append(text)
            break

        split_pos = text.rfind("\n", 0, max_length)
        if split_pos == -1:
            split_pos = max_length

        part = text[:split_pos]
        parts.append(part)
        text = text[split_pos:].lstrip("\n")

    return parts
