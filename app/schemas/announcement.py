from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class AnnouncementCreate(BaseModel):
    title: str
    content: str
    category: Optional[str] = None
    priority: str = "normal"
    target_audience: str = "all"
    target_tower: Optional[str] = None
    target_unit_id: Optional[UUID] = None

class AnnouncementResponse(BaseModel):
    id: UUID
    condominium_id: UUID
    created_by: UUID
    title: str
    content: str
    category: Optional[str]
    priority: str
    target_audience: str
    target_tower: Optional[str]
    target_unit_id: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True

