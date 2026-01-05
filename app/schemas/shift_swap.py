from pydantic import BaseModel
from typing import Optional, Dict
from uuid import UUID
from datetime import datetime

class ShiftSwapCreate(BaseModel):
    shift_id: UUID
    requested_to: Optional[UUID] = None  # Guardia específico (opcional, si es None, cualquier guardia puede aceptar)
    reason: Optional[str] = None

class ShiftSwapUpdate(BaseModel):
    status: Optional[str] = None  # approved, rejected
    admin_response: Optional[str] = None

class ShiftSwapResponse(BaseModel):
    id: UUID
    shift_id: UUID
    shift_info: Optional[Dict] = None  # Información del turno
    requested_by: UUID
    requester_name: Optional[str] = None
    requested_to: Optional[UUID] = None
    requested_to_name: Optional[str] = None
    status: str
    reason: Optional[str] = None
    admin_response: Optional[str] = None
    responded_by: Optional[UUID] = None
    responder_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    responded_at: Optional[datetime] = None

    class Config:
        from_attributes = True

