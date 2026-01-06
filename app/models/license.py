from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean
from app.models.uuid_helper import UUID, generate_uuid

from sqlalchemy.orm import relationship
from datetime import datetime

from app.db import Base

class License(Base):
    __tablename__ = "licenses"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    code = Column(String(50), unique=True, nullable=False, index=True)  # Código único de activación
    package_type = Column(String(50), nullable=False)  # "basic" ($40k), "intermediate" ($60k), "premium" ($80k)
    max_units = Column(Integer, nullable=True)  # Límite de unidades según paquete (null = ilimitado)
    max_users = Column(Integer, nullable=True)  # Límite de usuarios según paquete (null = ilimitado)
    
    # Estado de la licencia
    activated = Column(Boolean, default=False)  # Si ya fue activada
    activated_at = Column(DateTime, nullable=True)  # Fecha de activación
    activated_by = Column(UUID, ForeignKey("users.id"), nullable=True)  # Usuario que activó
    
    # Información de compra
    purchase_date = Column(DateTime, default=datetime.utcnow)  # Fecha de compra
    purchase_price = Column(Integer, nullable=True)  # Precio pagado (en centavos o pesos)
    buyer_name = Column(String(255), nullable=True)  # Nombre del comprador
    buyer_email = Column(String(255), nullable=True)  # Email del comprador
    
    # Expiración (opcional, para renovaciones anuales)
    expires_at = Column(DateTime, nullable=True)  # Si es null, no expira
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(String(500), nullable=True)  # Notas adicionales

    # Relaciones
    condominium = relationship("Condominium", back_populates="license", uselist=False)
    activator = relationship("User", foreign_keys=[activated_by])

