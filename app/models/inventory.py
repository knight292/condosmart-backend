from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, Boolean
from app.models.uuid_helper import UUID

from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db import Base

class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    condominium_id = Column(UUID, ForeignKey("condominiums.id"), nullable=False)
    created_by = Column(UUID, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))  # furniture, equipment, tools, etc.
    location = Column(String(255))  # área o unidad donde está
    quantity = Column(Integer, default=1)
    condition = Column(String(50))  # excellent, good, fair, poor
    purchase_date = Column(DateTime)
    purchase_price = Column(String(50))
    serial_number = Column(String(100))
    brand = Column(String(100))
    model = Column(String(100))
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    condominium = relationship("Condominium", back_populates="inventory_items")
    creator = relationship("User", back_populates="inventory_items_created")

