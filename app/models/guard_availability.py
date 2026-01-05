from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Date
import os
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test_condosmart.db")
USE_SQLITE = "sqlite" in DATABASE_URL
if USE_SQLITE:
    from sqlalchemy import String
    UUID = String(36)
else:
    UUID = PostgresUUID(as_uuid=True)

from app.db import USE_SQLITE
from sqlalchemy import String
UUID = String(36) if USE_SQLITE else PostgresUUID(as_uuid=True)
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db import Base

class GuardAvailability(Base):
    __tablename__ = "guard_availabilities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guard_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    condominium_id = Column(UUID(as_uuid=True), ForeignKey("condominiums.id"), nullable=False)
    date = Column(Date, nullable=False)  # Fecha específica
    is_available = Column(Boolean, default=True)  # True = disponible, False = no disponible
    preferred_shift_types = Column(String(200), nullable=True)  # JSON: ["morning", "afternoon"]
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    guard = relationship("User", back_populates="guard_availabilities")
    condominium = relationship("Condominium", back_populates="guard_availabilities")

