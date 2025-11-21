from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.orm import relationship
from src.infrastructure.postgres.connection import Base


class PollOption(Base):
    __tablename__ = "poll_options"

    id = Column(Integer, primary_key=True, autoincrement=True)
    poll_id = Column(Text, ForeignKey("polls.telegram_poll_id"))
    option_index = Column(Integer)
    option_text = Column(Text)

    poll = relationship("Poll", back_populates="options")
