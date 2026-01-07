from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID

from app.db import get_db
from app.models import Maintenance, User, Announcement
from app.schemas.maintenance import MaintenanceCreate, MaintenanceUpdate, MaintenanceResponse
from app.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=MaintenanceResponse, status_code=status.HTTP_201_CREATED)
def create_maintenance(
    maintenance_data: MaintenanceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create maintenances"
        )
    
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    # Convertir IDs a string si es SQLite
    condo_id = str(current_user.condominium_id) if (USE_SQLITE and current_user.condominium_id) else current_user.condominium_id
    user_id = str(current_user.id) if (USE_SQLITE and current_user.id) else current_user.id
    
    new_maintenance = Maintenance(
        condominium_id=condo_id,
        created_by=user_id,
        title=maintenance_data.title,
        description=maintenance_data.description,
        maintenance_type=maintenance_data.maintenance_type,
        area=maintenance_data.area,
        scheduled_date=maintenance_data.scheduled_date,
        cost=maintenance_data.cost,
        provider=maintenance_data.provider,
        notify_residents=maintenance_data.notify_residents
    )
    db.add(new_maintenance)
    db.commit()
    db.refresh(new_maintenance)
    
    # Crear aviso automático si se solicita notificación
    if maintenance_data.notify_residents:
        announcement = Announcement(
            condominium_id=condo_id,
            created_by=user_id,
            title=f"Mantenimiento Programado: {maintenance_data.title}",
            content=f"Se ha programado un mantenimiento para el {maintenance_data.scheduled_date.strftime('%d/%m/%Y')}. {maintenance_data.description or ''}",
            category="maintenance",
            priority="normal",
            target_audience="all"
        )
        db.add(announcement)
        db.commit()
    
    maintenance_dict = {
        "id": new_maintenance.id,
        "condominium_id": new_maintenance.condominium_id,
        "created_by": new_maintenance.created_by,
        "title": new_maintenance.title,
        "description": new_maintenance.description,
        "maintenance_type": new_maintenance.maintenance_type,
        "area": new_maintenance.area,
        "scheduled_date": new_maintenance.scheduled_date,
        "completed_date": new_maintenance.completed_date,
        "status": new_maintenance.status,
        "cost": new_maintenance.cost,
        "provider": new_maintenance.provider,
        "notify_residents": new_maintenance.notify_residents,
        "created_at": new_maintenance.created_at,
        "updated_at": new_maintenance.updated_at,
        "creator_name": current_user.full_name,
    }
    return maintenance_dict

@router.get("", response_model=List[MaintenanceResponse])
@router.get("/", response_model=List[MaintenanceResponse])
def get_maintenances(
    status_filter: Optional[str] = None,
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
    
    query = db.query(Maintenance).filter(
        Maintenance.condominium_id == condo_id
    )
    
    if status_filter:
        query = query.filter(Maintenance.status == status_filter)
    
    maintenances = query.order_by(Maintenance.scheduled_date.asc()).all()
    
    result = []
    for maint in maintenances:
        # Convertir ID para la query si es SQLite
        if USE_SQLITE:
            created_by_id = str(maint.created_by) if maint.created_by else None
        else:
            created_by_id = maint.created_by
        
        creator = db.query(User).filter(User.id == created_by_id).first() if created_by_id else None
        maint_dict = {
            "id": maint.id,
            "condominium_id": maint.condominium_id,
            "created_by": maint.created_by,
            "title": maint.title,
            "description": maint.description,
            "maintenance_type": maint.maintenance_type,
            "area": maint.area,
            "scheduled_date": maint.scheduled_date,
            "completed_date": maint.completed_date,
            "status": maint.status,
            "cost": maint.cost,
            "provider": maint.provider,
            "notify_residents": maint.notify_residents,
            "created_at": maint.created_at,
            "updated_at": maint.updated_at,
            "creator_name": creator.full_name if creator else None,
        }
        result.append(maint_dict)
    
    return result

@router.patch("/{maintenance_id}", response_model=MaintenanceResponse)
def update_maintenance(
    maintenance_id: str,
    maintenance_data: MaintenanceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update maintenances"
        )
    
    maint = db.query(Maintenance).filter(Maintenance.id == UUID(maintenance_id)).first()
    if not maint:
        raise HTTPException(status_code=404, detail="Maintenance not found")
    
    if maint.condominium_id != current_user.condominium_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = maintenance_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(maint, key, value)
    
    db.commit()
    db.refresh(maint)
    
    creator = db.query(User).filter(User.id == maint.created_by).first()
    maint_dict = {
        "id": maint.id,
        "condominium_id": maint.condominium_id,
        "created_by": maint.created_by,
        "title": maint.title,
        "description": maint.description,
        "maintenance_type": maint.maintenance_type,
        "area": maint.area,
        "scheduled_date": maint.scheduled_date,
        "completed_date": maint.completed_date,
        "status": maint.status,
        "cost": maint.cost,
        "provider": maint.provider,
        "notify_residents": maint.notify_residents,
        "created_at": maint.created_at,
        "updated_at": maint.updated_at,
        "creator_name": creator.full_name if creator else None,
    }
    return maint_dict

