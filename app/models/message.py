from sqlalchemy import Column, String, Text, Boolean, ForeignKey, DateTime
from app.models.uuid_helper import UUID, USE_SQLITE

from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db import Base

def generate_uuid():
    """Genera UUID como string para SQLite o como objeto UUID para PostgreSQL"""
    if USE_SQLITE:
        return str(uuid.uuid4())
    return uuid.uuid4()

class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    condominium_id = Column(UUID, ForeignKey("condominiums.id"), nullable=False)
    sender_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(UUID, ForeignKey("users.id"), nullable=True)
    conversation_type = Column(String(50), default="private")
    tower = Column(String(50))
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    condominium = relationship("Condominium", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id], back_populates="messages_sent")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="messages_received")

