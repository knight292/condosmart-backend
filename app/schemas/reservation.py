from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal

class ReservationCreate(BaseModel):
    facility_type: str
    start_time: datetime
    end_time: datetime
    unit_id: Optional[UUID] = None

class ReservationResponse(BaseModel):
    id: UUID
    condominium_id: UUID
    user_id: UUID
    unit_id: Optional[UUID]
    facility_type: str
    start_time: datetime
    end_time: datetime
    status: str
    cancellation_fee: Decimal
    created_at: datetime

    class Config:
        from_attributes = True

