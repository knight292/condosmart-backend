from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, date

from app.db import Base

class Contract(Base):
    __tablename__ = "contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    condominium_id = Column(UUID(as_uuid=True), ForeignKey("condominiums.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    contract_type = Column(String(100))  # service, supplier, maintenance, etc.
    provider_name = Column(String(255), nullable=False)
    provider_contact = Column(String(255))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    renewal_date = Column(Date)  # Fecha de renovación (1 mes antes de end_date)
    amount = Column(String(50))
    currency = Column(String(10), default="USD")
    status = Column(String(50), default="active")  # active, expired, renewed, cancelled
    auto_renew = Column(Boolean, default=False)
    file_path = Column(String(500))  # Archivo del contrato
    notification_sent = Column(Boolean, default=False)  # Si ya se envió notificación de renovación
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    condominium = relationship("Condominium", back_populates="contracts")
    creator = relationship("User", back_populates="contracts_created")

