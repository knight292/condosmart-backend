from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.models import Announcement, User
from app.schemas.announcement import AnnouncementCreate, AnnouncementResponse
from app.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
def create_announcement(
    announcement_data: AnnouncementCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create announcements"
        )
    
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    new_announcement = Announcement(
        condominium_id=current_user.condominium_id,
        created_by=current_user.id,
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
    return new_announcement

@router.get("/", response_model=List[AnnouncementResponse])
def get_announcements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    query = db.query(Announcement).filter(
        Announcement.condominium_id == current_user.condominium_id
    )
    
    if current_user.role == "resident":
        query = query.filter(
            (Announcement.target_audience == "all") |
            (Announcement.target_tower == current_user.unit.tower if current_user.unit else False) |
            (Announcement.target_unit_id == current_user.unit_id)
        )
    
    announcements = query.order_by(Announcement.created_at.desc()).all()
    return announcements

@router.get("/{announcement_id}", response_model=AnnouncementResponse)
def get_announcement(
    announcement_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found"
        )
    
    if announcement.condominium_id != current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    return announcement

