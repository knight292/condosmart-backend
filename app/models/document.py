from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer
from app.models.uuid_helper import UUID

from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    condominium_id = Column(UUID, ForeignKey("condominiums.id"), nullable=False)
    uploaded_by = Column(UUID, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer)  # en bytes
    file_type = Column(String(100))  # pdf, docx, etc.
    category = Column(String(100))  # legal, financial, maintenance, etc.
    is_public = Column(String(10), default="private")  # public, private, residents_only
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    condominium = relationship("Condominium", back_populates="documents")
    uploader = relationship("User", back_populates="documents_uploaded")

