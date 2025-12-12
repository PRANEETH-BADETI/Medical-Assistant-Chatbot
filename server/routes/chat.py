
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import crud.message as message_crud
import schemas.message as message_schemas
from utils.auth_deps import get_current_user
from models.user import User
from logger import logger

router = APIRouter(prefix="/chat", tags=["Chat History"])

@router.get("/history", response_model=List[message_schemas.MessageDisplay])
def get_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves the full chat history for the currently logged-in user.
    """
    logger.info(f"Fetching chat history for user: {current_user.email}")
    messages = message_crud.get_messages_by_user(db=db, user_id=current_user.id)
    return messages