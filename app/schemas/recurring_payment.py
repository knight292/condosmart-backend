from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal

class RecurringPaymentCreate(BaseModel):
    user_id: Optional[UUID] = None  # None = todos los residentes del condominio
    amount: Decimal
    currency: str = "MXN"
    description: str
    frequency: str  # "monthly", "quarterly", "yearly"
    day_of_month: int  # 1-31
    start_date: date
    end_date: Optional[date] = None  # None = indefinido

class RecurringPaymentUpdate(BaseModel):
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    description: Optional[str] = None
    frequency: Optional[str] = None
    day_of_month: Optional[int] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None

class RecurringPaymentResponse(BaseModel):
    id: UUID
    condominium_id: UUID
    user_id: Optional[UUID]
    amount: Decimal
    currency: str
    description: Optional[str]
    frequency: str
    day_of_month: int
    start_date: date
    end_date: Optional[date]
    is_active: bool
    last_generated: Optional[date]
    next_generation: Optional[date]
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    user_name: Optional[str] = None
    creator_name: Optional[str] = None

    class Config:
        from_attributes = True
