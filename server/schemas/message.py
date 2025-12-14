from pydantic import BaseModel
from datetime import datetime
from models.message import MessageRole

class MessageBase(BaseModel):
    content: str
    role: MessageRole

class MessageCreate(MessageBase):
    # We allow passing session_id explicitly if needed
    pass

class MessageDisplay(MessageBase):
    id: int
    session_id: int
    created_at: datetime

    class Config:
        from_attributes = True