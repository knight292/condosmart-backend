from sqlalchemy import Column, String, Numeric, Date, DateTime, ForeignKey, Integer, Boolean
from app.models.uuid_helper import UUID, generate_uuid
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db import Base

class RecurringPayment(Base):
    __tablename__ = "recurring_payments"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    condominium_id = Column(UUID, ForeignKey("condominiums.id"), nullable=False)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=True)  # None = todos los residentes
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="MXN")
    description = Column(String(255))  # Ej: "Cuota mensual de mantenimiento"
    
    # Configuración de recurrencia
    frequency = Column(String(20), nullable=False)  # "monthly", "quarterly", "yearly"
    day_of_month = Column(Integer, nullable=False)  # Día del mes (1-31)
    start_date = Column(Date, nullable=False)  # Fecha de inicio
    end_date = Column(Date, nullable=True)  # Fecha de fin (None = indefinido)
    
    # Estado
    is_active = Column(Boolean, default=True)
    last_generated = Column(Date)  # Última fecha en que se generó un pago
    next_generation = Column(Date)  # Próxima fecha en que se generará un pago
    
    # Metadatos
    created_by = Column(UUID, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    condominium = relationship("Condominium", back_populates="recurring_payments")
    user = relationship("User", foreign_keys=[user_id])
    creator = relationship("User", foreign_keys=[created_by])
