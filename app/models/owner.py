from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db import Base

class Owner(Base):
    """Dueño/empresa que puede tener múltiples condominios"""
    __tablename__ = "owners"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)  # Nombre de la empresa/dueño
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20))
    address = Column(String(500))
    tax_id = Column(String(50))  # RFC, NIT, etc.
    is_active = Column(String(50), default="active")  # active, suspended, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relación con condominios
    condominiums = relationship("Condominium", back_populates="owner")
    # Relación con usuarios owner
    users = relationship("User", back_populates="owner")

