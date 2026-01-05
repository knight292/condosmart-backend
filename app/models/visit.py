from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db import Base

class Visit(Base):
    __tablename__ = "visits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    condominium_id = Column(UUID(as_uuid=True), ForeignKey("condominiums.id"), nullable=False)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=False)
    visitor_name = Column(String(255), nullable=False)
    visitor_phone = Column(String(20))
    qr_code = Column(String(255), unique=True, nullable=False, index=True)
    status = Column(String(50), default="pending")
    entry_time = Column(DateTime)
    exit_time = Column(DateTime)
    scanned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    valid_until = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    condominium = relationship("Condominium", back_populates="visits")
    unit = relationship("Unit", back_populates="visits")
    resident = relationship("User", back_populates="visits")

