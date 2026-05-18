from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from app.db import get_db
from app.models import ShiftTemplate, User, GuardShift
from app.models.uuid_helper import USE_SQLITE
from app.schemas.shift_template import ShiftTemplateCreate, ShiftTemplateUpdate, ShiftTemplateResponse
from app.auth import get_current_user
from app.deps.modules import require_module
import json

router = APIRouter(dependencies=[Depends(require_module("guard_shifts"))])

@router.post("/", response_model=ShiftTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    template_data: ShiftTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["admin", "owner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create shift templates"
        )
    
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    # Convertir IDs a string si es SQLite
    condo_id = str(current_user.condominium_id) if (USE_SQLITE and current_user.condominium_id) else current_user.condominium_id
    user_id = str(current_user.id) if (USE_SQLITE and current_user.id) else current_user.id
    
    new_template = ShiftTemplate(
        condominium_id=condo_id,
        created_by=user_id,
        name=template_data.name,
        description=template_data.description,
        schedule=template_data.schedule  # Ya viene como lista de dicts
    )
    db.add(new_template)
    db.commit()
    db.refresh(new_template)
    
    return ShiftTemplateResponse(
        id=new_template.id,
        condominium_id=new_template.condominium_id,
        created_by=new_template.created_by,
        creator_name=current_user.full_name,
        name=new_template.name,
        description=new_template.description,
        schedule=new_template.schedule,
        is_active=new_template.is_active,
        created_at=new_template.created_at,
        updated_at=new_template.updated_at
    )

@router.post("/{template_id}/apply")
def apply_template(
    template_id: str,
    body: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_date_str = body.get("start_date")
    weeks = body.get("weeks", 1)
    """Aplica una plantilla de horarios creando turnos para las semanas especificadas"""
    if current_user.role not in ["admin", "owner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can apply templates"
        )
    
    # En SQLite, los IDs son strings, usar directamente
    # En PostgreSQL, convertir a UUID
    if USE_SQLITE:
        template_search_id = template_id
        condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
    else:
        from uuid import UUID
        try:
            template_search_id = UUID(template_id) if isinstance(template_id, str) else template_id
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid template ID format"
            )
        condo_id = current_user.condominium_id
    
    template = db.query(ShiftTemplate).filter(
        ShiftTemplate.id == template_search_id,
        ShiftTemplate.condominium_id == condo_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    if not template.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Template is not active"
        )
    
    created_shifts = 0
    errors = []
    
    if not start_date_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date is required"
        )
    
    # Parsear fecha de inicio
    try:
        week_start = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        if week_start.tzinfo:
            week_start = week_start.replace(tzinfo=None)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
        )
    
    # Aplicar para cada semana
    for week in range(weeks):
        week_start_actual = week_start + timedelta(weeks=week)
        
        # Para cada entrada en el schedule
        for entry in template.schedule:
            guard_id = entry.get("guard_id")
            day_of_week = entry.get("day_of_week")  # 0=Lunes, 6=Domingo
            shift_type = entry.get("shift_type")
            
            # Calcular la fecha del turno (día de la semana específico)
            days_to_add = day_of_week - week_start_actual.weekday()
            if days_to_add < 0:
                days_to_add += 7
            shift_date = week_start_actual + timedelta(days=days_to_add)
            
            # Convertir guard_id a string si es SQLite
            if USE_SQLITE:
                guard_search_id = str(guard_id) if guard_id else None
            else:
                guard_search_id = guard_id
            
            # Verificar que el guardia existe y pertenece al condominio
            guard = db.query(User).filter(
                User.id == guard_search_id,
                User.condominium_id == condo_id,
                User.role == "guard"
            ).first()
            
            if not guard:
                errors.append(f"Guard {guard_id} not found for entry on day {day_of_week}")
                continue
            
            # Verificar conflictos
            from app.routers.guard_shifts import _calculate_shift_times
            shift_start, shift_end = _calculate_shift_times(shift_date, shift_type)
            
            existing_shifts = db.query(GuardShift).filter(
                GuardShift.guard_id == guard_search_id,
                GuardShift.condominium_id == condo_id,
                GuardShift.status.in_(["scheduled", "active"])
            ).all()
            
            has_conflict = False
            for existing in existing_shifts:
                existing_start, existing_end = _calculate_shift_times(existing.shift_date, existing.shift_type)
                if (shift_start < existing_end and shift_end > existing_start):
                    has_conflict = True
                    break
            
            if has_conflict:
                errors.append(f"Conflict for guard {guard.full_name} on {shift_date.date()}")
                continue
            
            # Crear el turno
            new_shift = GuardShift(
                condominium_id=condo_id,
                guard_id=guard_search_id,
                shift_date=shift_date,
                shift_type=shift_type,
                status="scheduled"
            )
            db.add(new_shift)
            created_shifts += 1
    
    db.commit()
    
    return {
        "template_id": str(template.id),
        "template_name": template.name,
        "weeks_applied": weeks,
        "shifts_created": created_shifts,
        "errors": errors
    }

@router.get("", response_model=List[ShiftTemplateResponse])
@router.get("/", response_model=List[ShiftTemplateResponse])
def get_templates(
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
    
    templates = db.query(ShiftTemplate).filter(
        ShiftTemplate.condominium_id == condo_id
    ).order_by(ShiftTemplate.created_at.desc()).all()
    
    result = []
    for template in templates:
        # Convertir ID para la query si es SQLite
        if USE_SQLITE:
            created_by_id = str(template.created_by) if template.created_by else None
        else:
            created_by_id = template.created_by
        
        creator = db.query(User).filter(User.id == created_by_id).first() if created_by_id else None
        result.append(ShiftTemplateResponse(
            id=template.id,
            condominium_id=template.condominium_id,
            created_by=template.created_by,
            creator_name=creator.full_name if creator else None,
            name=template.name,
            description=template.description,
            schedule=template.schedule,
            is_active=template.is_active,
            created_at=template.created_at,
            updated_at=template.updated_at
        ))
    
    return result

@router.patch("/{template_id}", response_model=ShiftTemplateResponse)
def update_template(
    template_id: str,
    template_update: ShiftTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # En SQLite, los IDs son strings, usar directamente
    # En PostgreSQL, convertir a UUID
    if USE_SQLITE:
        template_search_id = template_id
        condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
    else:
        from uuid import UUID
        try:
            template_search_id = UUID(template_id) if isinstance(template_id, str) else template_id
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid template ID format"
            )
        condo_id = current_user.condominium_id
    
    template = db.query(ShiftTemplate).filter(
        ShiftTemplate.id == template_search_id,
        ShiftTemplate.condominium_id == condo_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    if template_update.name:
        template.name = template_update.name
    if template_update.description is not None:
        template.description = template_update.description
    if template_update.schedule:
        template.schedule = template_update.schedule
    if template_update.is_active is not None:
        template.is_active = template_update.is_active
    
    template.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(template)
    
    # Convertir ID para la query si es SQLite
    if USE_SQLITE:
        created_by_id = str(template.created_by) if template.created_by else None
    else:
        created_by_id = template.created_by
    
    creator = db.query(User).filter(User.id == created_by_id).first() if created_by_id else None
    return ShiftTemplateResponse(
        id=template.id,
        condominium_id=template.condominium_id,
        created_by=template.created_by,
        creator_name=creator.full_name if creator else None,
        name=template.name,
        description=template.description,
        schedule=template.schedule,
        is_active=template.is_active,
        created_at=template.created_at,
        updated_at=template.updated_at
    )

@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # En SQLite, los IDs son strings, usar directamente
    # En PostgreSQL, convertir a UUID
    if USE_SQLITE:
        template_search_id = template_id
        condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
    else:
        from uuid import UUID
        try:
            template_search_id = UUID(template_id) if isinstance(template_id, str) else template_id
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid template ID format"
            )
        condo_id = current_user.condominium_id
    
    template = db.query(ShiftTemplate).filter(
        ShiftTemplate.id == template_search_id,
        ShiftTemplate.condominium_id == condo_id
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    db.delete(template)
    db.commit()
    return None

