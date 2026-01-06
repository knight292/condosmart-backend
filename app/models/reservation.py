from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey
from app.models.uuid_helper import UUID, generate_uuid

from sqlalchemy.orm import relationship
from datetime import datetime

from app.db import Base

class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    condominium_id = Column(UUID, ForeignKey("condominiums.id"), nullable=False)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    unit_id = Column(UUID, ForeignKey("units.id"), nullable=True)
    facility_type = Column(String(50), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String(50), default="confirmed")
    cancellation_fee = Column(Numeric(10, 2), default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    condominium = relationship("Condominium", back_populates="reservations")
    user = relationship("User", back_populates="reservations")
    unit = relationship("Unit", back_populates="reservations")

