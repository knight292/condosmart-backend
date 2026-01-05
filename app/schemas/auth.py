from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None
    role: str
    condominium_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    phone: Optional[str]
    role: str
    condominium_id: Optional[UUID]
    unit_id: Optional[UUID]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

