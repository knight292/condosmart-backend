from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class PackageCreate(BaseModel):
    resident_id: UUID
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None

class PackageUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

class PackageResponse(BaseModel):
    id: UUID
    condominium_id: UUID
    resident_id: UUID
    resident_name: str
    received_by_id: Optional[UUID]
    received_by_name: Optional[str]
    carrier: Optional[str]
    tracking_number: Optional[str]
    description: Optional[str]
    status: str
    received_at: datetime
    picked_up_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

