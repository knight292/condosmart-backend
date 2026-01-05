from sqlalchemy import Column, String, Text, ForeignKey, DateTime
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

class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    condominium_id = Column(UUID(as_uuid=True), ForeignKey("condominiums.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50))
    priority = Column(String(50), default="normal")
    target_audience = Column(String(50), default="all")
    target_tower = Column(String(50))
    target_unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    condominium = relationship("Condominium", back_populates="announcements")
    creator = relationship("User", back_populates="announcements_created")

