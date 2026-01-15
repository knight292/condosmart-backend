from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON
from app.models.uuid_helper import UUID, generate_uuid
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    condominium_id = Column(UUID, ForeignKey("condominiums.id"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(String(1000), nullable=False)
    type = Column(String(50), nullable=False)
    action_id = Column(String(100), nullable=True)
    data = Column(JSON, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    condominium = relationship("Condominium")
