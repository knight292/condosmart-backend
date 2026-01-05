from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class MaintenanceCreate(BaseModel):
    title: str
    description: Optional[str] = None
    maintenance_type: Optional[str] = None
    area: Optional[str] = None
    scheduled_date: datetime
    cost: Optional[str] = None
    provider: Optional[str] = None
    notify_residents: bool = True

class MaintenanceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    maintenance_type: Optional[str] = None
    area: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    status: Optional[str] = None
    cost: Optional[str] = None
    provider: Optional[str] = None
    notify_residents: Optional[bool] = None

class MaintenanceResponse(BaseModel):
    id: UUID
    condominium_id: UUID
    created_by: UUID
    title: str
    description: Optional[str]
    maintenance_type: Optional[str]
    area: Optional[str]
    scheduled_date: datetime
    completed_date: Optional[datetime]
    status: str
    cost: Optional[str]
    provider: Optional[str]
    notify_residents: bool
    created_at: datetime
    updated_at: datetime
    creator_name: Optional[str] = None

    class Config:
        from_attributes = True

