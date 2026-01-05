from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class TicketAttachmentResponse(BaseModel):
    id: UUID
    file_url: str
    file_type: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class TicketCreate(BaseModel):
    category: Optional[str] = None
    title: str
    description: Optional[str] = None
    priority: str = "medium"

class TicketUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[UUID] = None
    priority: Optional[str] = None

class TicketResponse(BaseModel):
    id: UUID
    condominium_id: UUID
    reported_by: UUID
    category: Optional[str]
    title: str
    description: Optional[str]
    status: str
    assigned_to: Optional[UUID]
    priority: str
    resolved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    attachments: List[TicketAttachmentResponse] = []

    class Config:
        from_attributes = True

