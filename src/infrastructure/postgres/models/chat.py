from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Integer,
    Text,
)
from sqlalchemy.orm import relationship
from src.infrastructure.postgres.connection import Base


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_chat_id = Column(BigInteger, unique=True, nullable=False)
    title = Column(Text)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    polls = relationship("Poll", back_populates="chat", cascade="all, delete-orphan")
    code_lines = relationship("CodeLine", back_populates="chat", cascade="all, delete-orphan")
