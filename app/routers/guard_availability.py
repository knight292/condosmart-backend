from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime, timedelta
from app.db import get_db
from app.models import GuardAvailability, User
from app.schemas.guard_availability import GuardAvailabilityCreate, GuardAvailabilityUpdate, GuardAvailabilityResponse
from app.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=GuardAvailabilityResponse, status_code=status.HTTP_201_CREATED)
def create_availability(
    availability_data: GuardAvailabilityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "guard":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only guards can set their availability"
        )
    
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Guard must belong to a condominium"
        )
    
    # Verificar si ya existe disponibilidad para esta fecha
    existing = db.query(GuardAvailability).filter(
        GuardAvailability.guard_id == current_user.id,
        GuardAvailability.date == availability_data.date
    ).first()
    
    if existing:
        # Actualizar existente
        existing.is_available = availability_data.is_available
        existing.preferred_shift_types = ",".join(availability_data.preferred_shift_types) if availability_data.preferred_shift_types else None
        existing.notes = availability_data.notes
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        
        return GuardAvailabilityResponse(
            id=existing.id,
            guard_id=existing.guard_id,
            guard_name=current_user.full_name,
            condominium_id=existing.condominium_id,
            date=existing.date,
            is_available=existing.is_available,
            preferred_shift_types=existing.preferred_shift_types.split(",") if existing.preferred_shift_types else None,
            notes=existing.notes,
            created_at=existing.created_at,
            updated_at=existing.updated_at
        )
    
    new_availability = GuardAvailability(
        guard_id=current_user.id,
        condominium_id=current_user.condominium_id,
        date=availability_data.date,
        is_available=availability_data.is_available,
        preferred_shift_types=",".join(availability_data.preferred_shift_types) if availability_data.preferred_shift_types else None,
        notes=availability_data.notes
    )
    db.add(new_availability)
    db.commit()
    db.refresh(new_availability)
    
    return GuardAvailabilityResponse(
        id=new_availability.id,
        guard_id=new_availability.guard_id,
        guard_name=current_user.full_name,
        condominium_id=new_availability.condominium_id,
        date=new_availability.date,
        is_available=new_availability.is_available,
        preferred_shift_types=new_availability.preferred_shift_types.split(",") if new_availability.preferred_shift_types else None,
        notes=new_availability.notes,
        created_at=new_availability.created_at,
        updated_at=new_availability.updated_at
    )

@router.get("/", response_model=List[GuardAvailabilityResponse])
def get_availabilities(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    guard_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    query = db.query(GuardAvailability).filter(
        GuardAvailability.condominium_id == current_user.condominium_id
    )
    
    # Si es guardia, solo ver su propia disponibilidad
    if current_user.role == "guard":
        query = query.filter(GuardAvailability.guard_id == current_user.id)
    elif guard_id and current_user.role in ["admin", "super_admin", "owner"]:
        # Admin puede ver disponibilidad de un guardia específico
        from uuid import UUID
        try:
            guard_uuid = UUID(guard_id)
            query = query.filter(GuardAvailability.guard_id == guard_uuid)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid guard ID format"
            )
    
    if start_date:
        query = query.filter(GuardAvailability.date >= start_date)
    if end_date:
        query = query.filter(GuardAvailability.date <= end_date)
    
    availabilities = query.order_by(GuardAvailability.date.asc()).all()
    
    result = []
    for avail in availabilities:
        guard = db.query(User).filter(User.id == avail.guard_id).first()
        result.append(GuardAvailabilityResponse(
            id=avail.id,
            guard_id=avail.guard_id,
            guard_name=guard.full_name if guard else None,
            condominium_id=avail.condominium_id,
            date=avail.date,
            is_available=avail.is_available,
            preferred_shift_types=avail.preferred_shift_types.split(",") if avail.preferred_shift_types else None,
            notes=avail.notes,
            created_at=avail.created_at,
            updated_at=avail.updated_at
        ))
    
    return result

@router.delete("/{availability_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_availability(
    availability_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from uuid import UUID
    try:
        avail_uuid = UUID(availability_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid availability ID format"
        )
    
    availability = db.query(GuardAvailability).filter(GuardAvailability.id == avail_uuid).first()
    if not availability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Availability not found"
        )
    
    # Solo el guardia dueño o un admin puede eliminar
    if current_user.role == "guard" and availability.guard_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own availability"
        )
    
    if availability.condominium_id != current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    db.delete(availability)
    db.commit()
    return None

