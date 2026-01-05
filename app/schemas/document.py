from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class DocumentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    file_path: str
    file_name: str
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    category: Optional[str] = None
    is_public: str = "private"

class DocumentResponse(BaseModel):
    id: UUID
    condominium_id: UUID
    uploaded_by: UUID
    title: str
    description: Optional[str]
    file_path: str
    file_name: str
    file_size: Optional[int]
    file_type: Optional[str]
    category: Optional[str]
    is_public: str
    created_at: datetime
    updated_at: datetime
    uploader_name: Optional[str] = None

    class Config:
        from_attributes = True

