from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from src.application.enums import PollStatus


class PollResponseDTO(BaseModel):
    id: int
    chat_id: int
    telegram_poll_id: int
    question: str
    status: PollStatus
    created_at: datetime
    finished_at: Optional[datetime] = None


class PollCreateDTO(BaseModel):
    chat_id: int
    telegram_poll_id: int
    question: str
    status: Optional[PollStatus] = PollStatus.active.value
