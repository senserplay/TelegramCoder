from aiogram.types import Chat
from src.application.schemas.chat import ChatCreateDTO, ChatResponseDTO
from src.infrastructure.postgres.repositories.chat import ChatDBGateWay


class ChatService:
    def __init__(self, chat_gateway: ChatDBGateWay):
        self.chat_gateway = chat_gateway

    async def registration(self, chat: Chat) -> ChatResponseDTO:
        chat_data = ChatCreateDTO(
            telegram_chat_id=chat.id, title=chat.title if chat.title else chat.username
        )
        return await self.chat_gateway.get_or_create_chat(chat_data)

    async def delete_chat(self, telegram_chat_id) -> bool:
        if await self.chat_gateway.is_exist(telegram_chat_id):
            await self.chat_gateway.delete_chat(telegram_chat_id)
            return True
        return False
