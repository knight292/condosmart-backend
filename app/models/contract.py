from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean, Date
from app.models.uuid_helper import UUID, generate_uuid

from sqlalchemy.orm import relationship
from datetime import datetime, date

from app.db import Base

class Contract(Base):
    __tablename__ = "contracts"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    condominium_id = Column(UUID, ForeignKey("condominiums.id"), nullable=False)
    created_by = Column(UUID, ForeignKey("users.id"), nullable=False)
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

