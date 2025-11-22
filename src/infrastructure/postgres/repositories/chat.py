from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.errors.chat import ChatNotFoundException
from src.application.schemas.chat import ChatCreateDTO, ChatResponseDTO
from src.infrastructure.postgres.models.chat import Chat


class ChatDBGateWay:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_chat(self, telegram_chat_id: int) -> ChatResponseDTO:
        result = await self.session.execute(
            select(Chat).where(Chat.telegram_chat_id == telegram_chat_id)
        )
        chat: Chat = result.scalars().first()
        if chat is None:
            raise ChatNotFoundException()
        return ChatResponseDTO.model_validate(chat.as_dict())

    async def get_or_create_chat(self, chat_data: ChatCreateDTO) -> ChatResponseDTO:
        if await self.is_exist(chat_data.telegram_chat_id):
            return await self.get_chat(chat_data.telegram_chat_id)
        new_chat = Chat(**chat_data.model_dump())
        self.session.add(new_chat)
        await self.session.commit()
        await self.session.refresh(new_chat)

        return ChatResponseDTO.model_validate(new_chat.as_dict())

    async def is_exist(self, telegram_chat_id: int) -> bool:
        result = await self.session.execute(
            select(Chat).where(Chat.telegram_chat_id == telegram_chat_id)
        )
        chat: Chat = result.scalars().first()
        return bool(chat)

    async def delete_chat(self, telegram_chat_id: int):
        stmt = delete(Chat).where(Chat.telegram_chat_id == telegram_chat_id)
        await self.session.execute(stmt)
        await self.session.commit()
