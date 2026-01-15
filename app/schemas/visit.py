from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class VisitCreate(BaseModel):
    visitor_name: str
    visitor_phone: Optional[str] = None
    valid_until: datetime
    unit_id: Optional[UUID] = None

class VisitScan(BaseModel):
    qr_code: str

class VisitResponse(BaseModel):
    id: UUID
    condominium_id: UUID
    unit_id: UUID
    resident_id: Optional[UUID] = None
    visitor_name: str
    visitor_phone: Optional[str]
    qr_code: str
    status: str
    entry_time: Optional[datetime]
    exit_time: Optional[datetime]
    scanned_by: Optional[UUID]
    valid_until: datetime
    created_at: datetime

    class Config:
        from_attributes = True

