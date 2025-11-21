from datetime import datetime

from pydantic import BaseModel


class ChatResponseDTO(BaseModel):
    id: int
    telegram_chat_id: int
    title: str
    created_at: datetime


class ChatCreateDTO(BaseModel):
    telegram_chat_id: int
    title: str
