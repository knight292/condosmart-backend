from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class CondominiumCreate(BaseModel):
    name: str
    address: Optional[str] = None
    subscription_plan: Optional[str] = "basic"
    subscription_status: Optional[str] = "active"

class CondominiumUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    subscription_plan: Optional[str] = None
    subscription_status: Optional[str] = None

class CondominiumResponse(BaseModel):
    id: UUID
    name: str
    address: Optional[str]
    subscription_plan: Optional[str]
    subscription_status: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

