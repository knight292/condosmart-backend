from sqlalchemy import Column, String, Boolean, ForeignKey, Text
import os
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test_condosmart.db")
USE_SQLITE = "sqlite" in DATABASE_URL
if USE_SQLITE:
    from sqlalchemy import String
    UUID = String(36)
else:
    UUID = PostgresUUID(as_uuid=True)

from app.db import USE_SQLITE
from sqlalchemy import String
UUID = String(36) if USE_SQLITE else PostgresUUID(as_uuid=True)
from sqlalchemy.orm import relationship
import uuid

from app.db import Base

class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    condominium_id = Column(UUID(as_uuid=True), ForeignKey("condominiums.id"), nullable=False)
    
    # Tipo de método: 'bank_deposit', 'card', 'spei', 'oxxo', 'cash', etc.
    method_type = Column(String(50), nullable=False)
    
    # Nombre descriptivo del método
    name = Column(String(255), nullable=False)
    
    # Información específica según el tipo
    # Para depósitos bancarios: número de cuenta, banco, CLABE, etc.
    account_number = Column(String(100), nullable=True)
    bank_name = Column(String(255), nullable=True)
    clabe = Column(String(18), nullable=True)  # CLABE bancaria
    account_holder = Column(String(255), nullable=True)  # Titular de la cuenta
    
    # Para pasarelas de pago: configuración del gateway
    gateway_name = Column(String(50), nullable=True)  # 'stripe', 'mercadopago', etc.
    gateway_config = Column(Text, nullable=True)  # JSON con configuración
    
    # Estado y configuración
    is_active = Column(Boolean, default=True)
    requires_verification = Column(Boolean, default=False)  # Si requiere verificación manual
    instructions = Column(Text, nullable=True)  # Instrucciones para el residente
    
    # Relación
    condominium = relationship("Condominium", back_populates="payment_methods")

