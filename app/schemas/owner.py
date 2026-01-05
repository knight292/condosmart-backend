from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class OwnerCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None

class OwnerResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None
    is_active: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class CondominiumSummary(BaseModel):
    id: str
    name: str
    address: Optional[str] = None
    subscription_status: str
    users_count: int
    created_at: Optional[str] = None

