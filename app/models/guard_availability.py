from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Date
from app.models.uuid_helper import UUID

from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db import Base

class GuardAvailability(Base):
    __tablename__ = "guard_availabilities"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    guard_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    condominium_id = Column(UUID, ForeignKey("condominiums.id"), nullable=False)
    date = Column(Date, nullable=False)  # Fecha específica
    is_available = Column(Boolean, default=True)  # True = disponible, False = no disponible
    preferred_shift_types = Column(String(200), nullable=True)  # JSON: ["morning", "afternoon"]
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    guard = relationship("User", back_populates="guard_availabilities")
    condominium = relationship("Condominium", back_populates="guard_availabilities")

