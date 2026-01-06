from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from app.models.uuid_helper import UUID, generate_uuid

from sqlalchemy.orm import relationship
from datetime import datetime

from app.db import Base

class ShiftSwap(Base):
    __tablename__ = "shift_swaps"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    shift_id = Column(UUID, ForeignKey("guard_shifts.id"), nullable=False)
    requested_by = Column(UUID, ForeignKey("users.id"), nullable=False)  # Guardia que solicita
    requested_to = Column(UUID, ForeignKey("users.id"), nullable=True)  # Guardia específico (opcional)
    status = Column(String(50), default="pending")  # pending, approved, rejected, cancelled
    reason = Column(String(500), nullable=True)
    admin_response = Column(String(500), nullable=True)
    responded_by = Column(UUID, ForeignKey("users.id"), nullable=True)  # Admin que respondió
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    responded_at = Column(DateTime, nullable=True)

    shift = relationship("GuardShift", back_populates="swap_requests")
    requester = relationship("User", foreign_keys=[requested_by], back_populates="shift_swaps_requested")
    responder = relationship("User", foreign_keys=[responded_by], back_populates="shift_swaps_responded")

