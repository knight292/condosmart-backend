from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import get_db
from app.models import Notification, User
from app.models.uuid_helper import USE_SQLITE
from app.schemas.notification import NotificationResponse
from app.auth import get_current_user

router = APIRouter()


@router.get("", response_model=List[NotificationResponse])
@router.get("/", response_model=List[NotificationResponse])
def get_notifications(
    unread_only: Optional[bool] = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Convertir IDs a string si es SQLite
    if USE_SQLITE:
        user_id = str(current_user.id) if current_user.id else None
    else:
        user_id = current_user.id

    query = db.query(Notification).filter(Notification.user_id == user_id)
    if unread_only:
        query = query.filter(Notification.is_read == False)

    notifications = query.order_by(Notification.created_at.desc()).all()
    return notifications


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Convertir IDs a string si es SQLite
    if USE_SQLITE:
        user_id = str(current_user.id) if current_user.id else None
        notif_id = notification_id
    else:
        from uuid import UUID
        try:
            notif_id = UUID(notification_id) if isinstance(notification_id, str) else notification_id
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid notification ID format"
            )
        user_id = current_user.id

    notification = db.query(Notification).filter(
        Notification.id == notif_id,
        Notification.user_id == user_id
    ).first()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


@router.patch("/read-all", status_code=status.HTTP_204_NO_CONTENT)
def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Convertir IDs a string si es SQLite
    if USE_SQLITE:
        user_id = str(current_user.id) if current_user.id else None
    else:
        user_id = current_user.id

    db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return None
