from sqlalchemy import Column, String, Numeric, Date, DateTime, ForeignKey
from app.models.uuid_helper import UUID, generate_uuid

from sqlalchemy.orm import relationship
from datetime import datetime

from app.db import Base

class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    condominium_id = Column(UUID, ForeignKey("condominiums.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="MXN")
    status = Column(String(50), default="pending")
    payment_method = Column(String(50))
    payment_gateway = Column(String(50))
    gateway_transaction_id = Column(String(255))
    due_date = Column(Date)
    paid_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="payments")
    condominium = relationship("Condominium", back_populates="payments")

