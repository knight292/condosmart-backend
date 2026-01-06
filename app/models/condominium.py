from sqlalchemy import Column, String, DateTime, ForeignKey
from app.models.uuid_helper import UUID, generate_uuid

from sqlalchemy.orm import relationship
from datetime import datetime

from app.db import Base

class Condominium(Base):
    __tablename__ = "condominiums"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    owner_id = Column(UUID, ForeignKey("owners.id"), nullable=True)  # Dueño del condominio
    license_id = Column(UUID, ForeignKey("licenses.id"), nullable=True)  # Licencia asociada
    name = Column(String(255), nullable=False)
    address = Column(String(500))
    subscription_plan = Column(String(50))
    subscription_status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("Owner", back_populates="condominiums")
    users = relationship("User", back_populates="condominium")
    units = relationship("Unit", back_populates="condominium")
    payments = relationship("Payment", back_populates="condominium")
    tickets = relationship("Ticket", back_populates="condominium")
    visits = relationship("Visit", back_populates="condominium")
    reservations = relationship("Reservation", back_populates="condominium")
    announcements = relationship("Announcement", back_populates="condominium")
    messages = relationship("Message", back_populates="condominium")
    documents = relationship("Document", back_populates="condominium")
    maintenances = relationship("Maintenance", back_populates="condominium")
    contracts = relationship("Contract", back_populates="condominium")
    inventory_items = relationship("InventoryItem", back_populates="condominium")
    regulations = relationship("Regulation", back_populates="condominium")
    guard_shifts = relationship("GuardShift", back_populates="condominium")
    guard_availabilities = relationship("GuardAvailability", back_populates="condominium")
    shift_templates = relationship("ShiftTemplate", back_populates="condominium")
    packages = relationship("Package", back_populates="condominium")
    payment_methods = relationship("PaymentMethod", back_populates="condominium", cascade="all, delete-orphan")
    license = relationship("License", back_populates="condominium", uselist=False, foreign_keys=[license_id])

