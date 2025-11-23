from datetime import datetime

from pydantic import BaseModel


class CodeLineResponseDTO(BaseModel):
    id: int
    chat_id: int
    poll_id: int
    line_number: int
    content: str
    created_at: datetime


class CodeLineCreateDTO(BaseModel):
    chat_id: int
    poll_id: str
    line_number: int
    content: str
