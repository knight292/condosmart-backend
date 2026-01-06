from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean
from app.models.uuid_helper import UUID, generate_uuid

from sqlalchemy.orm import relationship
from datetime import datetime

from app.db import Base

class Package(Base):
    __tablename__ = "packages"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    condominium_id = Column(UUID, ForeignKey("condominiums.id"), nullable=False)
    resident_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    received_by_id = Column(UUID, ForeignKey("users.id"), nullable=True)  # Guardia o admin que recibió
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

