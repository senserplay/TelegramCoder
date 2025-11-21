import json
from logging import Logger

from aiogram import Router
from aiogram.filters import ADMINISTRATOR, IS_MEMBER, IS_NOT_MEMBER, KICKED, ChatMemberUpdatedFilter
from aiogram.types import Chat, ChatMemberUpdated
from dishka import FromDishka
from src.services.chat import ChatService


router = Router()


@router.my_chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed=(IS_NOT_MEMBER | ADMINISTRATOR) >> (IS_MEMBER | ADMINISTRATOR)
    )
)
async def on_bot_added(
    update: ChatMemberUpdated, logger: FromDishka[Logger], chat_service: FromDishka[ChatService]
):
    bot = await update.bot.get_me()
    if update.new_chat_member.user.id != bot.id:
        return

    chat_id = update.chat.id

    try:
        chat_info: Chat = await update.bot.get_chat(chat_id)
        chat = await chat_service.registration(chat_info)

        logger.info(f"Бот добавлен в чат. Полная информация о чате ID {chat.telegram_chat_id}:")
        logger.info(chat.model_dump())

        message_text = (
            f"🎉 Бот успешно добавлен в группу!\n\n"
            f"📋 Информация о чате:\n"
            f"🆔 ID: {chat_info.id}\n"
            f"🏷️ Название: {chat_info.title or 'Без названия'}\n"
            f"👥 Тип: {chat_info.type}\n"
            f"ℹ️ Подробная информация залогирована в консоль."
        )

        await update.bot.send_message(chat_id, message_text)

    except Exception as e:
        logger.error(f"Ошибка при получении информации о чате {chat_id}: {str(e)}")
        await update.bot.send_message(
            chat_id,
            f"👋 Привет! Спасибо, что добавили меня в группу!\n\n"
            f"⚠️ Не удалось получить полную информацию о чате из-за ошибки: {str(e)}",
        )


@router.my_chat_member(
    ChatMemberUpdatedFilter(
        member_status_changed=(IS_MEMBER | ADMINISTRATOR) >> (IS_NOT_MEMBER | KICKED)
    )
)
async def on_bot_kicked(
    update: ChatMemberUpdated, logger: FromDishka[Logger], chat_service: FromDishka[ChatService]
):
    bot = await update.bot.get_me()
    if update.new_chat_member.user.id != bot.id:
        return

    chat_id = update.chat.id
    old_status = update.old_chat_member.status
    new_status = update.new_chat_member.status

    try:
        chat_info: Chat = await update.bot.get_chat(chat_id)
        chat_title = chat_info.title or "Без названия"

        if await chat_service.delete_chat(chat_id):
            logger.info(f"Чат {chat_id} удален из БД")
        else:
            logger.error(f"Не удалось удалить чат {chat_id} из БД")

        logger.info(f"Статусы: old='{old_status}', new='{new_status}'")

        deletion_details = {
            "chat_id": chat_id,
            "chat_title": chat_title,
            "old_status": old_status,
            "new_status": new_status,
            "user_id": update.from_user.id if update.from_user else None,
            "user_name": (
                update.from_user.full_name if update.from_user else "Неизвестный пользователь"
            ),
            "event_date": update.date.isoformat(),
        }
        logger.info(
            f"Детали удаления чата: {json.dumps(deletion_details, indent=2, ensure_ascii=False)}"
        )

    except Exception as e:
        logger.error(f"Ошибка при обработке кика из чата {chat_id}: {str(e)}")
        if await chat_service.delete_chat(chat_id):
            logger.info(f"Чат {chat_id} был удален из БД несмотря на ошибку")
        else:
            logger.error(f"Критическая ошибка: не удалось удалить чат {chat_id} из БД")
