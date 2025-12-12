# server/models/message.py

import enum
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)

    content = Column(Text, nullable=False)

    role = Column(Enum(MessageRole), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # --- Foreign Key to link to the User table ---
    owner_id = Column(Integer, ForeignKey("users.id"))

    # --- Relationship (for easy access from the User object) ---
    owner = relationship("User")