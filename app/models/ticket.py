from sqlalchemy import Column, String, Text, ForeignKey, DateTime
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

class Ticket(Base):
    __tablename__ = "maintenance_tickets"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    condominium_id = Column(UUID, ForeignKey("condominiums.id"), nullable=False)
    reported_by = Column(UUID, ForeignKey("users.id"), nullable=False)
    category = Column(String(50))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="new")
    assigned_to = Column(UUID, ForeignKey("users.id"), nullable=True)
    priority = Column(String(50), default="medium")
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    condominium = relationship("Condominium", back_populates="tickets")
    reporter = relationship("User", foreign_keys=[reported_by], back_populates="tickets_reported")
    assignee = relationship("User", foreign_keys=[assigned_to], back_populates="tickets_assigned")
    attachments = relationship("TicketAttachment", back_populates="ticket", cascade="all, delete-orphan")

class TicketAttachment(Base):
    __tablename__ = "ticket_attachments"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    ticket_id = Column(UUID, ForeignKey("maintenance_tickets.id"), nullable=False)
    file_url = Column(Text, nullable=False)
    file_type = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="attachments")

