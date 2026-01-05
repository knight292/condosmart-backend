from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from app.models.uuid_helper import UUID

from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db import Base

class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    condominium_id = Column(UUID, ForeignKey("condominiums.id"), nullable=False)
    created_by = Column(UUID, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50))
    priority = Column(String(50), default="normal")
    target_audience = Column(String(50), default="all")
    target_tower = Column(String(50))
    target_unit_id = Column(UUID, ForeignKey("units.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    condominium = relationship("Condominium", back_populates="announcements")
    creator = relationship("User", back_populates="announcements_created")

