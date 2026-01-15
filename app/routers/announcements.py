from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.models import Announcement, User, Unit, Notification
from app.models.uuid_helper import USE_SQLITE
from app.schemas.announcement import AnnouncementCreate, AnnouncementResponse
from app.auth import get_current_user

router = APIRouter()

@router.post("", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
def create_announcement(
    announcement_data: AnnouncementCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create announcements"
        )
    
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    # Convertir IDs a string si es SQLite
    condo_id = str(current_user.condominium_id) if (USE_SQLITE and current_user.condominium_id) else current_user.condominium_id
    user_id = str(current_user.id) if (USE_SQLITE and current_user.id) else current_user.id
    
    new_announcement = Announcement(
        condominium_id=condo_id,
        created_by=user_id,
        title=announcement_data.title,
        content=announcement_data.content,
        category=announcement_data.category,
        priority=announcement_data.priority,
        target_audience=announcement_data.target_audience,
        target_tower=announcement_data.target_tower,
        target_unit_id=announcement_data.target_unit_id
    )
    db.add(new_announcement)
    db.commit()
    db.refresh(new_announcement)
    
    # Crear notificaciones para destinatarios del aviso
    try:
        users_query = db.query(User).filter(User.condominium_id == condo_id)
        if announcement_data.target_audience and announcement_data.target_audience != "all":
            role_map = {
                "residents": "resident",
                "guards": "guard",
                "admins": "admin",
                "owners": "owner",
            }
            target_role = role_map.get(announcement_data.target_audience)
            if target_role:
                users_query = users_query.filter(User.role == target_role)
        
        if announcement_data.target_unit_id:
            users_query = users_query.filter(User.unit_id == announcement_data.target_unit_id)
        elif announcement_data.target_tower:
            users_query = users_query.filter(User.unit.has(Unit.tower == announcement_data.target_tower))
        
        recipients = users_query.all()
        notifications = []
        for user in recipients:
            user_id_value = str(user.id) if USE_SQLITE else user.id
            notifications.append(Notification(
                user_id=user_id_value,
                condominium_id=condo_id,
                title="Nuevo aviso",
                message=new_announcement.title,
                type="announcement",
                action_id=str(new_announcement.id),
                data={"announcement_id": str(new_announcement.id)}
            ))
        if notifications:
            db.add_all(notifications)
            db.commit()
    except Exception as e:
        print(f"⚠️ No se pudieron crear notificaciones de aviso: {e}")
    return new_announcement

@router.get("", response_model=List[AnnouncementResponse])
@router.get("/", response_model=List[AnnouncementResponse])
def get_announcements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Super_admin no debe acceder a avisos de condominios
    if current_user.role == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin cannot access condominium announcements"
        )
    
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    # Convertir IDs a string si es SQLite
    condo_id = str(current_user.condominium_id) if (USE_SQLITE and current_user.condominium_id) else current_user.condominium_id
    unit_id = str(current_user.unit_id) if (USE_SQLITE and current_user.unit_id) else current_user.unit_id
    
    query = db.query(Announcement).filter(
        Announcement.condominium_id == condo_id
    )
    
    if current_user.role == "resident":
        # Construir filtros para residentes
        filters = [Announcement.target_audience == "all"]
        if current_user.unit and current_user.unit.tower:
            filters.append(Announcement.target_tower == current_user.unit.tower)
        if unit_id:
            filters.append(Announcement.target_unit_id == unit_id)
        
        from sqlalchemy import or_
        query = query.filter(or_(*filters))
    
    announcements = query.order_by(Announcement.created_at.desc()).all()
    return announcements

@router.get("/{announcement_id}", response_model=AnnouncementResponse)
def get_announcement(
    announcement_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Super_admin no debe acceder a avisos de condominios
    if current_user.role == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin cannot access condominium announcements"
        )
    
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found"
        )
    
    # Convertir IDs a string si es SQLite para comparación
    if USE_SQLITE:
        condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
        announcement_condo_id = str(announcement.condominium_id) if announcement.condominium_id else None
    else:
        condo_id = current_user.condominium_id
        announcement_condo_id = announcement.condominium_id
    
    if announcement_condo_id != condo_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    return announcement

