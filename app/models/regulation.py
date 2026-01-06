from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean, Date
from app.models.uuid_helper import UUID, generate_uuid

from sqlalchemy.orm import relationship
from datetime import datetime

from app.db import Base

class Regulation(Base):
    __tablename__ = "regulations"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    condominium_id = Column(UUID, ForeignKey("condominiums.id"), nullable=False)
    created_by = Column(UUID, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100))  # general, pets, parking, noise, etc.
    effective_date = Column(Date, nullable=False)
    file_path = Column(String(500))  # Archivo PDF del reglamento
    notify_users = Column(Boolean, default=True)
    notification_sent = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    condominium = relationship("Condominium", back_populates="regulations")
    creator = relationship("User", back_populates="regulations_created")

