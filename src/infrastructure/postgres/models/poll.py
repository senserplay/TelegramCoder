from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship
from src.application.enums import PollStatus
from src.infrastructure.postgres.connection import Base


class Poll(Base):
    __tablename__ = "polls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, ForeignKey("chats.telegram_chat_id"))
    telegram_poll_id = Column(Text, unique=True, nullable=False)
    question = Column(Text)
    status = Column(ENUM(PollStatus, name="poll_status_type"), default="active")
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    finished_at = Column(DateTime, nullable=True)

    chat = relationship("Chat", back_populates="polls")
    options = relationship("PollOption", back_populates="poll", cascade="all, delete-orphan")
    code_lines = relationship("CodeLine", back_populates="poll", cascade="all, delete-orphan")
