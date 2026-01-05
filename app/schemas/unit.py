from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class UnitCreate(BaseModel):
    condominium_id: UUID
    number: str
    tower: Optional[str] = None
    floor: Optional[int] = None
    type: Optional[str] = None  # apartment, house, commercial, etc.

class UnitUpdate(BaseModel):
    number: Optional[str] = None
    tower: Optional[str] = None
    floor: Optional[int] = None
    type: Optional[str] = None

class UnitResponse(BaseModel):
    id: UUID
    condominium_id: UUID
    number: str
    tower: Optional[str]
    floor: Optional[int]
    type: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

