# server/crud/message.py

from sqlalchemy.orm import Session
from models.message import Message, MessageRole
from schemas.message import MessageCreate
from logger import logger

def create_message(db: Session, message: MessageCreate, user_id: int) -> Message:
    """
    Saves a new chat message to the database.
    """
    db_message = Message(
        content=message.content,
        role=message.role,
        owner_id=user_id
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    logger.debug(f"Saved message (ID: {db_message.id}) for user {user_id}")
    return db_message

def get_messages_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> list[Message]:
    """
    Retrieves all chat messages for a specific user.
    """
    return (
        db.query(Message)
        .filter(Message.owner_id == user_id)
        .order_by(Message.created_at.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )