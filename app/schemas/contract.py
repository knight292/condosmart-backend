from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from uuid import UUID

class ContractCreate(BaseModel):
    title: str
    description: Optional[str] = None
    contract_type: Optional[str] = None
    provider_name: str
    provider_contact: Optional[str] = None
    start_date: date
    end_date: date
    amount: Optional[str] = None
    currency: str = "USD"
    auto_renew: bool = False
    file_path: Optional[str] = None

class ContractUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    contract_type: Optional[str] = None
    provider_name: Optional[str] = None
    provider_contact: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    renewal_date: Optional[date] = None
    amount: Optional[str] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    auto_renew: Optional[bool] = None
    file_path: Optional[str] = None

class ContractResponse(BaseModel):
    id: UUID
    condominium_id: UUID
    created_by: UUID
    title: str
    description: Optional[str]
    contract_type: Optional[str]
    provider_name: str
    provider_contact: Optional[str]
    start_date: date
    end_date: date
    renewal_date: Optional[date]
    amount: Optional[str]
    currency: str
    status: str
    auto_renew: bool
    file_path: Optional[str]
    notification_sent: bool
    created_at: datetime
    updated_at: datetime
    creator_name: Optional[str] = None
    days_until_renewal: Optional[int] = None

    class Config:
        from_attributes = True

