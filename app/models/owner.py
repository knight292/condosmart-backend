from sqlalchemy import Column, String, DateTime, ForeignKey
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

