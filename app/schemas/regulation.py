from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from uuid import UUID

class RegulationCreate(BaseModel):
    title: str
    content: str
    category: Optional[str] = None
    effective_date: date
    file_path: Optional[str] = None
    notify_users: bool = True

class RegulationUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    effective_date: Optional[date] = None
    file_path: Optional[str] = None
    is_active: Optional[bool] = None
    notify_users: Optional[bool] = None

class RegulationResponse(BaseModel):
    id: UUID
    condominium_id: UUID
    created_by: UUID
    title: str
    content: str
    category: Optional[str]
    effective_date: date
    file_path: Optional[str]
    notify_users: bool
    notification_sent: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    creator_name: Optional[str] = None

    class Config:
        from_attributes = True

