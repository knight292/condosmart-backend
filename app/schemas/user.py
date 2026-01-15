from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None
    role: str
    condominium_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    fcm_token: Optional[str] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    fcm_token: Optional[str] = None
    unit_id: Optional[UUID] = None  # Permitir cambiar la unidad del usuario
    role: Optional[str] = None  # Permitir cambiar el rol (solo super_admin)

class FcmTokenUpdate(BaseModel):
    fcm_token: Optional[str] = None

class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    phone: Optional[str] = None
    role: str
    condominium_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
