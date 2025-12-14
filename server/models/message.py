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

    # --- Foreign Keys ---
    # Link to the specific chat session
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)

    # We keep owner_id for easy access, though technically accessible via session
    owner_id = Column(Integer, ForeignKey("users.id"))

    # --- Relationships ---
    session = relationship("ChatSession", back_populates="messages")
    owner = relationship("User")