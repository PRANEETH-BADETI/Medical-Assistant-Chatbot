from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class ChatSessionBase(BaseModel):
    title: str = "New Chat"

class ChatSessionCreate(ChatSessionBase):
    pass

class ChatSession(ChatSessionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True