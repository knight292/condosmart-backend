from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, JSON, Boolean
from app.models.uuid_helper import UUID

from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db import Base

class ShiftTemplate(Base):
    __tablename__ = "shift_templates"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    condominium_id = Column(UUID, ForeignKey("condominiums.id"), nullable=False)
    created_by = Column(UUID, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)  # "Horario Semanal", "Turnos Mensuales"
    description = Column(String(500), nullable=True)
    # JSON array de asignaciones: [{"guard_id": "...", "day_of_week": 0-6, "shift_type": "morning", "time": "06:00"}]
    schedule = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    condominium = relationship("Condominium", back_populates="shift_templates")
    creator = relationship("User", back_populates="shift_templates_created")

