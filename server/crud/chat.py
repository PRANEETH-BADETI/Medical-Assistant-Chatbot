from sqlalchemy.orm import Session
from models.chat import ChatSession
from schemas.chat import ChatSessionCreate
from logger import logger

def create_session(db: Session, session: ChatSessionCreate, user_id: int):
    db_session = ChatSession(
        user_id=user_id,
        title=session.title
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    logger.info(f"Created new chat session {db_session.id} for user {user_id}")
    return db_session

def get_user_sessions(db: Session, user_id: int, skip: int = 0, limit: int = 50):
    return (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_session(db: Session, session_id: int, user_id: int):
    return db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id
    ).first()

def delete_session(db: Session, session_id: int, user_id: int):
    session = get_session(db, session_id, user_id)
    if session:
        db.delete(session)
        db.commit()
        return True
    return False

def update_session_title(db: Session, session_id: int, title: str, user_id: int):
    session = get_session(db, session_id, user_id)
    if session:
        session.title = title
        db.commit()
        db.refresh(session)
        return session
    return None