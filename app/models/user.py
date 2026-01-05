from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20))
    fcm_token = Column(String(500), nullable=True)  # Token para Firebase Cloud Messaging
    role = Column(String(50), nullable=False)  # owner, super_admin, admin, resident, guard
    owner_id = Column(UUID(as_uuid=True), ForeignKey("owners.id"), nullable=True)  # Para usuarios owner
    condominium_id = Column(UUID(as_uuid=True), ForeignKey("condominiums.id"), nullable=True)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("Owner", back_populates="users")
    condominium = relationship("Condominium", back_populates="users")
    unit = relationship("Unit", back_populates="residents")
    payments = relationship("Payment", back_populates="user")
    tickets_reported = relationship("Ticket", foreign_keys="Ticket.reported_by", back_populates="reporter")
    tickets_assigned = relationship("Ticket", foreign_keys="Ticket.assigned_to", back_populates="assignee")
    visits = relationship("Visit", back_populates="resident")
    reservations = relationship("Reservation", back_populates="user")
    announcements_created = relationship("Announcement", back_populates="creator")
    messages_sent = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    messages_received = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver")
    documents_uploaded = relationship("Document", back_populates="uploader")
    maintenances_created = relationship("Maintenance", back_populates="creator")
    contracts_created = relationship("Contract", back_populates="creator")
    inventory_items_created = relationship("InventoryItem", back_populates="creator")
    regulations_created = relationship("Regulation", back_populates="creator")
    guard_shifts = relationship("GuardShift", back_populates="guard")
    guard_availabilities = relationship("GuardAvailability", back_populates="guard")
    shift_templates_created = relationship("ShiftTemplate", back_populates="creator")
    shift_swaps_requested = relationship("ShiftSwap", foreign_keys="ShiftSwap.requested_by", back_populates="requester")
    shift_swaps_responded = relationship("ShiftSwap", foreign_keys="ShiftSwap.responded_by", back_populates="responder")
    packages_received = relationship("Package", foreign_keys="Package.resident_id", back_populates="resident")

