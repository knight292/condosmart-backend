from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db import Base

class GuardShift(Base):
    __tablename__ = "guard_shifts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    condominium_id = Column(UUID(as_uuid=True), ForeignKey("condominiums.id"), nullable=False)
    guard_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    shift_date = Column(DateTime, nullable=False)  # Fecha y hora del turno
    shift_type = Column(String(50), nullable=False)  # morning, afternoon, night, full_day
    status = Column(String(50), default="scheduled")  # scheduled, active, completed, cancelled
    notes = Column(String(500), nullable=True)
    check_in_time = Column(DateTime, nullable=True)  # Hora de entrada
    check_out_time = Column(DateTime, nullable=True)  # Hora de salida
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    condominium = relationship("Condominium", back_populates="guard_shifts")
    guard = relationship("User", back_populates="guard_shifts")
    swap_requests = relationship("ShiftSwap", back_populates="shift")

