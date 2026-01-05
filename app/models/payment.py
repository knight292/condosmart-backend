from sqlalchemy import Column, String, Numeric, Date, DateTime, ForeignKey
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

class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    condominium_id = Column(UUID(as_uuid=True), ForeignKey("condominiums.id"), nullable=False)
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

