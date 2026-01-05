from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime

class GuardAvailabilityCreate(BaseModel):
    date: date
    is_available: bool = True
    preferred_shift_types: Optional[List[str]] = None
    notes: Optional[str] = None

class GuardAvailabilityUpdate(BaseModel):
    is_available: Optional[bool] = None
    preferred_shift_types: Optional[List[str]] = None
    notes: Optional[str] = None

class GuardAvailabilityResponse(BaseModel):
    id: UUID
    guard_id: UUID
    guard_name: Optional[str] = None
    condominium_id: UUID
    date: date
    is_available: bool
    preferred_shift_types: Optional[List[str]] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

