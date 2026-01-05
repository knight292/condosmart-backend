from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db import Base

class Unit(Base):
    __tablename__ = "units"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    condominium_id = Column(UUID(as_uuid=True), ForeignKey("condominiums.id"), nullable=False)
    number = Column(String(50), nullable=False)
    tower = Column(String(50))
    floor = Column(Integer)
    type = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    condominium = relationship("Condominium", back_populates="units")
    residents = relationship("User", back_populates="unit")
    visits = relationship("Visit", back_populates="unit")
    reservations = relationship("Reservation", back_populates="unit")

