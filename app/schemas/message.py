from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class MessageCreate(BaseModel):
    receiver_id: Optional[UUID] = None
    conversation_type: str = "private"
    tower: Optional[str] = None
    content: str

class MessageResponse(BaseModel):
    id: UUID
    condominium_id: UUID
    sender_id: UUID
    receiver_id: Optional[UUID]
    conversation_type: str
    tower: Optional[str]
    content: str
    is_read: bool
    created_at: datetime
    sender_name: Optional[str] = None

    class Config:
        from_attributes = True

