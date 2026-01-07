from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime, timedelta
from app.db import get_db
from app.models import GuardAvailability, User
from app.models.uuid_helper import USE_SQLITE
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
    
    # Convertir IDs a string si es SQLite
    if USE_SQLITE:
        guard_id = str(current_user.id) if current_user.id else None
        condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
    else:
        guard_id = current_user.id
        condo_id = current_user.condominium_id
    
    # Verificar si ya existe disponibilidad para esta fecha
    existing = db.query(GuardAvailability).filter(
        GuardAvailability.guard_id == guard_id,
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
        guard_id=guard_id,
        condominium_id=condo_id,
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

@router.get("", response_model=List[GuardAvailabilityResponse])
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
    
    # Convertir condominium_id a string si es SQLite
    if USE_SQLITE:
        condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
        user_id = str(current_user.id) if current_user.id else None
    else:
        condo_id = current_user.condominium_id
        user_id = current_user.id
    
    query = db.query(GuardAvailability).filter(
        GuardAvailability.condominium_id == condo_id
    )
    
    # Si es guardia, solo ver su propia disponibilidad
    if current_user.role == "guard":
        query = query.filter(GuardAvailability.guard_id == user_id)
    elif guard_id and current_user.role in ["admin", "owner"]:
        # Admin puede ver disponibilidad de un guardia específico
        if USE_SQLITE:
            guard_search_id = guard_id
        else:
            from uuid import UUID
            try:
                guard_search_id = UUID(guard_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid guard ID format"
                )
        query = query.filter(GuardAvailability.guard_id == guard_search_id)
    
    if start_date:
        query = query.filter(GuardAvailability.date >= start_date)
    if end_date:
        query = query.filter(GuardAvailability.date <= end_date)
    
    availabilities = query.order_by(GuardAvailability.date.asc()).all()
    
    result = []
    for avail in availabilities:
        # Convertir ID para la query si es SQLite
        if USE_SQLITE:
            guard_search_id = str(avail.guard_id) if avail.guard_id else None
        else:
            guard_search_id = avail.guard_id
        
        guard = db.query(User).filter(User.id == guard_search_id).first() if guard_search_id else None
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
    # En SQLite, los IDs son strings, usar directamente
    # En PostgreSQL, convertir a UUID
    if USE_SQLITE:
        avail_search_id = availability_id
    else:
        from uuid import UUID
        try:
            avail_search_id = UUID(availability_id) if isinstance(availability_id, str) else availability_id
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid availability ID format"
            )
    
    availability = db.query(GuardAvailability).filter(GuardAvailability.id == avail_search_id).first()
    if not availability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Availability not found"
        )
    
    # Convertir IDs para comparación si es SQLite
    if USE_SQLITE:
        avail_guard_id = str(availability.guard_id) if availability.guard_id else None
        user_id = str(current_user.id) if current_user.id else None
        avail_condo_id = str(availability.condominium_id) if availability.condominium_id else None
        user_condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
    else:
        avail_guard_id = availability.guard_id
        user_id = current_user.id
        avail_condo_id = availability.condominium_id
        user_condo_id = current_user.condominium_id
    
    # Solo el guardia dueño o un admin puede eliminar
    if current_user.role == "guard" and avail_guard_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own availability"
        )
    
    if avail_condo_id != user_condo_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    db.delete(availability)
    db.commit()
    return None

