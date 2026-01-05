from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

class ScheduleEntry(BaseModel):
    guard_id: UUID
    day_of_week: int  # 0=Lunes, 6=Domingo
    shift_type: str  # morning, afternoon, night, full_day
    time: Optional[str] = None  # "06:00"

class ShiftTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    schedule: List[Dict[str, Any]]  # Lista de ScheduleEntry como dicts

class ShiftTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    schedule: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None

class ShiftTemplateResponse(BaseModel):
    id: UUID
    condominium_id: UUID
    created_by: UUID
    creator_name: Optional[str] = None
    name: str
    description: Optional[str] = None
    schedule: List[Dict[str, Any]]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

