from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

class LicenseBase(BaseModel):
    package_type: str  # "basic", "intermediate", "premium"
    max_units: Optional[int] = None
    max_users: Optional[int] = None
    buyer_name: Optional[str] = None
    buyer_email: Optional[EmailStr] = None
    purchase_price: Optional[int] = None
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None

class LicenseCreate(LicenseBase):
    pass

class LicenseActivate(BaseModel):
    code: str
    condominium_name: str
    condominium_address: Optional[str] = None

class LicenseActivatePublic(BaseModel):
    code: str
    condominium_name: str
    condominium_address: Optional[str] = None
    admin_name: str
    admin_email: EmailStr
    admin_password: str
    admin_phone: Optional[str] = None

class LicenseResponse(BaseModel):
    id: UUID
    code: str
    package_type: str
    max_units: Optional[int] = None
    max_users: Optional[int] = None
    activated: bool
    activated_at: Optional[datetime] = None
    purchase_date: datetime
    expires_at: Optional[datetime] = None
    condominium_id: Optional[UUID] = None
    
    class Config:
        from_attributes = True

class LicenseValidation(BaseModel):
    valid: bool
    code: str
    package_type: Optional[str] = None
    activated: bool = False
    condominium_name: Optional[str] = None
    message: str

