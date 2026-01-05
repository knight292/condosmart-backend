from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class GuardShiftCreate(BaseModel):
    shift_date: datetime
    shift_type: str  # morning, afternoon, night, full_day
    guard_id: Optional[UUID] = None  # Para admins: especificar guardia. Si es None, usa el usuario actual
    notes: Optional[str] = None

class GuardShiftUpdate(BaseModel):
    status: Optional[str] = None
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    notes: Optional[str] = None

class GuardShiftResponse(BaseModel):
    id: UUID
    condominium_id: UUID
    guard_id: UUID
    guard_name: Optional[str] = None
    shift_date: datetime
    shift_type: str
    status: str
    notes: Optional[str] = None
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    shift_start: Optional[datetime] = None
    shift_end: Optional[datetime] = None

    class Config:
        from_attributes = True

