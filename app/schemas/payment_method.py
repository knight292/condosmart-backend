from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class PaymentMethodCreate(BaseModel):
    method_type: str  # 'bank_deposit', 'card', 'spei', 'oxxo', etc.
    name: str
    account_number: Optional[str] = None
    bank_name: Optional[str] = None
    clabe: Optional[str] = None
    account_holder: Optional[str] = None
    gateway_name: Optional[str] = None
    gateway_config: Optional[str] = None
    requires_verification: bool = False
    instructions: Optional[str] = None
    is_active: bool = True

class PaymentMethodUpdate(BaseModel):
    name: Optional[str] = None
    account_number: Optional[str] = None
    bank_name: Optional[str] = None
    clabe: Optional[str] = None
    account_holder: Optional[str] = None
    gateway_config: Optional[str] = None
    requires_verification: Optional[bool] = None
    instructions: Optional[str] = None
    is_active: Optional[bool] = None

class PaymentMethodResponse(BaseModel):
    id: UUID
    condominium_id: UUID
    method_type: str
    name: str
    account_number: Optional[str]
    bank_name: Optional[str]
    clabe: Optional[str]
    account_holder: Optional[str]
    gateway_name: Optional[str]
    requires_verification: bool
    instructions: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True

