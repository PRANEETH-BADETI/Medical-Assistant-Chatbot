# server/schemas/message.py

from pydantic import BaseModel
from datetime import datetime
from models.message import MessageRole

class MessageBase(BaseModel):
    content: str
    role: MessageRole

class MessageCreate(MessageBase):
    pass # Nothing extra needed to create

class MessageDisplay(MessageBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True