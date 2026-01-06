from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid

from app.db import get_db
from app.models import Document, User
from app.models.uuid_helper import USE_SQLITE
from app.schemas.document import DocumentCreate, DocumentResponse
from app.auth import get_current_user

router = APIRouter()

UPLOAD_DIR = "uploads/documents"

@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    file: UploadFile = File(...),
    title: str = None,
    description: Optional[str] = None,
    category: Optional[str] = None,
    is_public: str = "private",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can upload documents"
        )
    
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    # Crear directorio si no existe
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Guardar archivo
    file_extension = os.path.splitext(file.filename)[1]
    file_name = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, file_name)
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Convertir IDs a string si es SQLite
    condo_id = str(current_user.condominium_id) if (USE_SQLITE and current_user.condominium_id) else current_user.condominium_id
    user_id = str(current_user.id) if (USE_SQLITE and current_user.id) else current_user.id
    
    new_document = Document(
        condominium_id=condo_id,
        uploaded_by=user_id,
        title=title or file.filename,
        description=description,
        file_path=file_path,
        file_name=file.filename,
        file_size=len(content),
        file_type=file.content_type,
        category=category,
        is_public=is_public
    )
    db.add(new_document)
    db.commit()
    db.refresh(new_document)
    
    document_dict = {
        "id": new_document.id,
        "condominium_id": new_document.condominium_id,
        "uploaded_by": new_document.uploaded_by,
        "title": new_document.title,
        "description": new_document.description,
        "file_path": new_document.file_path,
        "file_name": new_document.file_name,
        "file_size": new_document.file_size,
        "file_type": new_document.file_type,
        "category": new_document.category,
        "is_public": new_document.is_public,
        "created_at": new_document.created_at,
        "updated_at": new_document.updated_at,
        "uploader_name": current_user.full_name,
    }
    return document_dict

@router.get("", response_model=List[DocumentResponse])
@router.get("/", response_model=List[DocumentResponse])
def get_documents(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    # Convertir condominium_id a string si es SQLite
    if USE_SQLITE:
        condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
    else:
        condo_id = current_user.condominium_id
    
    query = db.query(Document).filter(
        Document.condominium_id == condo_id
    )
    
    # Si es residente, solo documentos públicos
    if current_user.role == "resident":
        query = query.filter(Document.is_public.in_(["public", "residents_only"]))
    
    if category:
        query = query.filter(Document.category == category)
    
    documents = query.order_by(Document.created_at.desc()).all()
    
    result = []
    for doc in documents:
        # Convertir ID para la query si es SQLite
        if USE_SQLITE:
            uploaded_by_id = str(doc.uploaded_by) if doc.uploaded_by else None
        else:
            uploaded_by_id = doc.uploaded_by
        
        uploader = db.query(User).filter(User.id == uploaded_by_id).first() if uploaded_by_id else None
        doc_dict = {
            "id": doc.id,
            "condominium_id": doc.condominium_id,
            "uploaded_by": doc.uploaded_by,
            "title": doc.title,
            "description": doc.description,
            "file_path": doc.file_path,
            "file_name": doc.file_name,
            "file_size": doc.file_size,
            "file_type": doc.file_type,
            "category": doc.category,
            "is_public": doc.is_public,
            "created_at": doc.created_at,
            "updated_at": doc.updated_at,
            "uploader_name": uploader.full_name if uploader else None,
        }
        result.append(doc_dict)
    
    return result

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete documents"
        )
    
    from uuid import UUID
    doc = db.query(Document).filter(Document.id == UUID(document_id)).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if doc.condominium_id != current_user.condominium_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Eliminar archivo
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    
    db.delete(doc)
    db.commit()
    return None

