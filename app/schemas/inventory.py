from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class InventoryItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    quantity: int = 1
    condition: Optional[str] = None
    purchase_date: Optional[datetime] = None
    purchase_price: Optional[str] = None
    serial_number: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    notes: Optional[str] = None

class InventoryItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    quantity: Optional[int] = None
    condition: Optional[str] = None
    purchase_date: Optional[datetime] = None
    purchase_price: Optional[str] = None
    serial_number: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None

class InventoryItemResponse(BaseModel):
    id: UUID
    condominium_id: UUID
    created_by: UUID
    name: str
    description: Optional[str]
    category: Optional[str]
    location: Optional[str]
    quantity: int
    condition: Optional[str]
    purchase_date: Optional[datetime]
    purchase_price: Optional[str]
    serial_number: Optional[str]
    brand: Optional[str]
    model: Optional[str]
    is_active: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    creator_name: Optional[str] = None

    class Config:
        from_attributes = True

