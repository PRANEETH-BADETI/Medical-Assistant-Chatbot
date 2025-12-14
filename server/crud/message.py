from sqlalchemy.orm import Session
from models.message import Message, MessageRole
from schemas.message import MessageCreate
from logger import logger

def create_message(db: Session, message: MessageCreate, user_id: int, session_id: int) -> Message:
    db_message = Message(
        content=message.content,
        role=message.role,
        owner_id=user_id,
        session_id=session_id
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_messages_by_session(db: Session, session_id: int, user_id: int):
    """Retrieves messages for a specific session, verifying ownership."""
    # We join with ChatSession to ensure the user owns this session
    return (
        db.query(Message)
        .join(Message.session)
        .filter(Message.session_id == session_id)
        .filter(Message.owner_id == user_id)
        .order_by(Message.created_at.asc())
        .all()
    )