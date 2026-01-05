from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean
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

class Maintenance(Base):
    __tablename__ = "maintenances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    condominium_id = Column(UUID(as_uuid=True), ForeignKey("condominiums.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    maintenance_type = Column(String(100))  # preventive, corrective, emergency
    area = Column(String(100))  # elevators, pool, garden, etc.
    scheduled_date = Column(DateTime, nullable=False)
    completed_date = Column(DateTime, nullable=True)
    status = Column(String(50), default="scheduled")  # scheduled, in_progress, completed, cancelled
    cost = Column(String(50))
    provider = Column(String(255))
    notify_residents = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    condominium = relationship("Condominium", back_populates="maintenances")
    creator = relationship("User", back_populates="maintenances_created")

