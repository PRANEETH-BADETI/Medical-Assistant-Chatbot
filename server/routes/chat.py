from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import crud.chat as chat_crud
import crud.message as message_crud
import schemas.chat as chat_schemas
import schemas.message as message_schemas
from utils.auth_deps import get_current_user
from models.user import User

router = APIRouter(prefix="/chat", tags=["Chat Sessions"])


# --- Session Management ---

@router.post("/sessions", response_model=chat_schemas.ChatSession)
def create_new_session(
        session_data: chat_schemas.ChatSessionCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    return chat_crud.create_session(db, session_data, current_user.id)


@router.get("/sessions", response_model=List[chat_schemas.ChatSession])
def get_my_sessions(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    return chat_crud.get_user_sessions(db, current_user.id)


@router.delete("/sessions/{session_id}")
def delete_session(
        session_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    success = chat_crud.delete_session(db, session_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session deleted"}


# --- Message History for a Session ---

@router.get("/sessions/{session_id}/messages", response_model=List[message_schemas.MessageDisplay])
def get_session_history(
        session_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # Check if session exists and belongs to user
    session = chat_crud.get_session(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return message_crud.get_messages_by_session(db, session_id, current_user.id)