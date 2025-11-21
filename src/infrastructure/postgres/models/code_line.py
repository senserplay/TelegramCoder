from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.orm import relationship
from src.infrastructure.postgres.connection import Base


class CodeLine(Base):
    __tablename__ = "code_lines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, ForeignKey("chats.telegram_chat_id"))
    poll_id = Column(Text, ForeignKey("polls.telegram_poll_id"))
    line_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    chat = relationship("Chat", back_populates="code_lines")
    poll = relationship("Poll", back_populates="code_lines")
