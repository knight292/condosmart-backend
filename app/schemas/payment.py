from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal

class PaymentCreate(BaseModel):
    user_id: Optional[UUID] = None  # ID del usuario para quien se crea el pago (requerido para admins)
    amount: Decimal
    currency: str = "MXN"
    payment_method: Optional[str] = None
    due_date: date
    description: Optional[str] = None  # Descripción del pago (ej: "Cuota mensual enero 2024")

class PaymentProcess(BaseModel):
    payment_method_id: str  # ID del método de pago seleccionado
    notes: Optional[str] = None  # Notas adicionales (ej: número de referencia de depósito)

class PaymentResponse(BaseModel):
    id: UUID
    user_id: UUID
    condominium_id: UUID
    amount: Decimal
    currency: str
    status: str
    description: Optional[str] = None
    payment_method: Optional[str]
    payment_gateway: Optional[str]
    gateway_transaction_id: Optional[str]
    due_date: Optional[date]
    paid_at: Optional[datetime]
    created_at: datetime
    user_name: Optional[str] = None  # Nombre del residente
    user_email: Optional[str] = None  # Email del residente

    class Config:
        from_attributes = True

