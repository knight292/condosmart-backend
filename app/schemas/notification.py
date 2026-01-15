from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    condominium_id: UUID
    title: str
    message: str
    type: str
    action_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    is_read: bool = False
    created_at: datetime

    class Config:
        from_attributes = True
