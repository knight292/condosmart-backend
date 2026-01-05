from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db import Base

class Package(Base):
    __tablename__ = "packages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    condominium_id = Column(UUID(as_uuid=True), ForeignKey("condominiums.id"), nullable=False)
    resident_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    received_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # Guardia o admin que recibió
    carrier = Column(String(255))  # Empresa de envío (DHL, FedEx, etc.)
    tracking_number = Column(String(255))
    description = Column(Text)
    status = Column(String(50), default="pending")  # pending, received, picked_up, returned
    received_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    picked_up_at = Column(DateTime, nullable=True)
    notes = Column(Text)  # Notas adicionales del guardia/admin
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    condominium = relationship("Condominium", back_populates="packages")
    resident = relationship("User", foreign_keys=[resident_id], back_populates="packages_received")
    received_by = relationship("User", foreign_keys=[received_by_id])

