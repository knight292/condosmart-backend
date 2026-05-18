from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.db import get_db
from app.models import Regulation, User, Announcement
from app.models.uuid_helper import USE_SQLITE
from app.schemas.regulation import RegulationCreate, RegulationUpdate, RegulationResponse
from app.auth import get_current_user
from app.deps.modules import require_module

router = APIRouter(dependencies=[Depends(require_module("regulations"))])

@router.post("/", response_model=RegulationResponse, status_code=status.HTTP_201_CREATED)
def create_regulation(
    regulation_data: RegulationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create regulations"
        )
    
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    # Convertir IDs a string si es SQLite
    condo_id = str(current_user.condominium_id) if (USE_SQLITE and current_user.condominium_id) else current_user.condominium_id
    user_id = str(current_user.id) if (USE_SQLITE and current_user.id) else current_user.id
    
    new_regulation = Regulation(
        condominium_id=condo_id,
        created_by=user_id,
        title=regulation_data.title,
        content=regulation_data.content,
        category=regulation_data.category,
        effective_date=regulation_data.effective_date,
        file_path=regulation_data.file_path,
        notify_users=regulation_data.notify_users
    )
    db.add(new_regulation)
    db.commit()
    db.refresh(new_regulation)
    
    # Crear aviso automático si se solicita notificación
    if regulation_data.notify_users:
        announcement = Announcement(
            condominium_id=condo_id,
            created_by=user_id,
            title=f"Nuevo Reglamento: {regulation_data.title}",
            content=f"Se ha publicado un nuevo reglamento. {regulation_data.content[:200]}...",
            category="regulation",
            priority="high",
            target_audience="all"
        )
        db.add(announcement)
        new_regulation.notification_sent = True
        db.commit()
    
    regulation_dict = {
        "id": new_regulation.id,
        "condominium_id": new_regulation.condominium_id,
        "created_by": new_regulation.created_by,
        "title": new_regulation.title,
        "content": new_regulation.content,
        "category": new_regulation.category,
        "effective_date": new_regulation.effective_date,
        "file_path": new_regulation.file_path,
        "notify_users": new_regulation.notify_users,
        "notification_sent": new_regulation.notification_sent,
        "is_active": new_regulation.is_active,
        "created_at": new_regulation.created_at,
        "updated_at": new_regulation.updated_at,
        "creator_name": current_user.full_name,
    }
    return regulation_dict

@router.get("", response_model=List[RegulationResponse])
@router.get("/", response_model=List[RegulationResponse])
def get_regulations(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    # Convertir ID a string si es SQLite
    condo_id = str(current_user.condominium_id) if (USE_SQLITE and current_user.condominium_id) else current_user.condominium_id
    
    query = db.query(Regulation).filter(
        Regulation.condominium_id == condo_id,
        Regulation.is_active == True
    )
    
    if category:
        query = query.filter(Regulation.category == category)
    
    regulations = query.order_by(Regulation.effective_date.desc()).all()
    
    result = []
    for reg in regulations:
        # Convertir ID para la query si es SQLite
        if USE_SQLITE:
            created_by_id = str(reg.created_by) if reg.created_by else None
        else:
            created_by_id = reg.created_by
        
        creator = db.query(User).filter(User.id == created_by_id).first() if created_by_id else None
        reg_dict = {
            "id": reg.id,
            "condominium_id": reg.condominium_id,
            "created_by": reg.created_by,
            "title": reg.title,
            "content": reg.content,
            "category": reg.category,
            "effective_date": reg.effective_date,
            "file_path": reg.file_path,
            "notify_users": reg.notify_users,
            "notification_sent": reg.notification_sent,
            "is_active": reg.is_active,
            "created_at": reg.created_at,
            "updated_at": reg.updated_at,
            "creator_name": creator.full_name if creator else None,
        }
        result.append(reg_dict)
    
    return result

@router.get("/{regulation_id}", response_model=RegulationResponse)
def get_regulation(
    regulation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    regulation = db.query(Regulation).filter(Regulation.id == UUID(regulation_id)).first()
    
    if not regulation:
        raise HTTPException(status_code=404, detail="Regulation not found")
    
    # Convertir IDs a string si es SQLite para comparación
    if USE_SQLITE:
        condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
        regulation_condo_id = str(regulation.condominium_id) if regulation.condominium_id else None
        created_by_id = str(regulation.created_by) if regulation.created_by else None
    else:
        condo_id = current_user.condominium_id
        regulation_condo_id = regulation.condominium_id
        created_by_id = regulation.created_by
    
    if regulation_condo_id != condo_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    creator = db.query(User).filter(User.id == created_by_id).first() if created_by_id else None
    reg_dict = {
        "id": regulation.id,
        "condominium_id": regulation.condominium_id,
        "created_by": regulation.created_by,
        "title": regulation.title,
        "content": regulation.content,
        "category": regulation.category,
        "effective_date": regulation.effective_date,
        "file_path": regulation.file_path,
        "notify_users": regulation.notify_users,
        "notification_sent": regulation.notification_sent,
        "is_active": regulation.is_active,
        "created_at": regulation.created_at,
        "updated_at": regulation.updated_at,
        "creator_name": creator.full_name if creator else None,
    }
    return reg_dict

@router.patch("/{regulation_id}", response_model=RegulationResponse)
def update_regulation(
    regulation_id: str,
    regulation_data: RegulationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update regulations"
        )
    
    regulation = db.query(Regulation).filter(Regulation.id == UUID(regulation_id)).first()
    if not regulation:
        raise HTTPException(status_code=404, detail="Regulation not found")
    
    # Convertir IDs a string si es SQLite para comparación
    if USE_SQLITE:
        condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
        regulation_condo_id = str(regulation.condominium_id) if regulation.condominium_id else None
        user_id = str(current_user.id) if current_user.id else None
        created_by_id = str(regulation.created_by) if regulation.created_by else None
    else:
        condo_id = current_user.condominium_id
        regulation_condo_id = regulation.condominium_id
        user_id = current_user.id
        created_by_id = regulation.created_by
    
    if regulation_condo_id != condo_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = regulation_data.dict(exclude_unset=True)
    
    # Si se actualiza y se solicita notificar, crear aviso
    if "notify_users" in update_data and update_data["notify_users"] and not regulation.notification_sent:
        announcement = Announcement(
            condominium_id=condo_id,
            created_by=user_id,
            title=f"Actualización de Reglamento: {regulation.title}",
            content=f"Se ha actualizado el reglamento. Por favor revisa los cambios.",
            category="regulation",
            priority="high",
            target_audience="all"
        )
        db.add(announcement)
        update_data["notification_sent"] = True
    
    for key, value in update_data.items():
        setattr(regulation, key, value)
    
    db.commit()
    db.refresh(regulation)
    
    creator = db.query(User).filter(User.id == created_by_id).first() if created_by_id else None
    reg_dict = {
        "id": regulation.id,
        "condominium_id": regulation.condominium_id,
        "created_by": regulation.created_by,
        "title": regulation.title,
        "content": regulation.content,
        "category": regulation.category,
        "effective_date": regulation.effective_date,
        "file_path": regulation.file_path,
        "notify_users": regulation.notify_users,
        "notification_sent": regulation.notification_sent,
        "is_active": regulation.is_active,
        "created_at": regulation.created_at,
        "updated_at": regulation.updated_at,
        "creator_name": creator.full_name if creator else None,
    }
    return reg_dict

