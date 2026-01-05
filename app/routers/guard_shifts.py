from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta
from app.db import get_db
from app.models import GuardShift, User
from app.schemas.guard_shift import GuardShiftCreate, GuardShiftResponse, GuardShiftUpdate
from app.auth import get_current_user
from app.services.email_service import EmailService
from app.services.fcm_service import FCMService

router = APIRouter()

def _calculate_shift_times(shift_date: datetime, shift_type: str):
    """Calcula shift_start y shift_end basado en shift_date y shift_type"""
    if shift_type == "morning":
        shift_start = shift_date.replace(hour=6, minute=0, second=0, microsecond=0)
        shift_end = shift_date.replace(hour=14, minute=0, second=0, microsecond=0)
    elif shift_type == "afternoon":
        shift_start = shift_date.replace(hour=14, minute=0, second=0, microsecond=0)
        shift_end = shift_date.replace(hour=22, minute=0, second=0, microsecond=0)
    elif shift_type == "night":
        shift_start = shift_date.replace(hour=22, minute=0, second=0, microsecond=0)
        shift_end = (shift_date + timedelta(days=1)).replace(hour=6, minute=0, second=0, microsecond=0)
    elif shift_type == "full_day":
        shift_start = shift_date.replace(hour=6, minute=0, second=0, microsecond=0)
        shift_end = shift_date.replace(hour=22, minute=0, second=0, microsecond=0)
    else:
        # Default: usar shift_date como inicio y agregar 8 horas
        shift_start = shift_date
        shift_end = shift_date + timedelta(hours=8)
    
    return shift_start, shift_end

@router.post("/", response_model=GuardShiftResponse, status_code=status.HTTP_201_CREATED)
def create_guard_shift(
    shift_data: GuardShiftCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Permitir que admins asignen turnos a guardias, o guardias se auto-asignen
    if current_user.role not in ["admin", "super_admin", "owner", "guard"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins or guards can create shifts"
        )
    
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )

    # Determinar el guard_id: si es admin/owner y se especifica, usar ese; si no, usar el usuario actual
    guard_id = shift_data.guard_id if shift_data.guard_id else current_user.id
    
    # Si un admin está asignando a otro guardia, verificar que el guardia pertenece al mismo condominio
    if current_user.role in ["admin", "super_admin", "owner"] and shift_data.guard_id:
        assigned_guard = db.query(User).filter(
            User.id == guard_id,
            User.condominium_id == current_user.condominium_id,
            User.role == "guard"
        ).first()
        if not assigned_guard:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Guard not found or does not belong to this condominium"
            )
    elif current_user.role == "guard":
        # Guardias solo pueden asignarse a sí mismos
        guard_id = current_user.id

    # Verificar conflictos: el guardia no debe tener otro turno en el mismo rango de tiempo
    shift_start, shift_end = _calculate_shift_times(shift_data.shift_date, shift_data.shift_type)
    
    # Buscar turnos existentes del guardia
    existing_shifts = db.query(GuardShift).filter(
        GuardShift.guard_id == guard_id,
        GuardShift.condominium_id == current_user.condominium_id,
        GuardShift.status.in_(["scheduled", "active"])
    ).all()
    
    # Verificar solapamiento con cada turno existente
    conflicting_shift = None
    for existing in existing_shifts:
        existing_start, existing_end = _calculate_shift_times(existing.shift_date, existing.shift_type)
        # Verificar si hay solapamiento
        if (shift_start < existing_end and shift_end > existing_start):
            conflicting_shift = existing
            break
    
    if conflicting_shift:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Guard already has a shift scheduled for this time period"
        )

    new_shift = GuardShift(
        condominium_id=current_user.condominium_id,
        guard_id=guard_id,
        shift_date=shift_data.shift_date,
        shift_type=shift_data.shift_type,
        notes=shift_data.notes,
        status="scheduled"
    )
    db.add(new_shift)
    db.commit()
    db.refresh(new_shift)
    
    # Notificación: Si un admin asignó el turno, notificar al guardia
    if current_user.role in ["admin", "super_admin", "owner"] and guard_id != current_user.id:
        assigned_guard = db.query(User).filter(User.id == guard_id).first()
        if assigned_guard:
            shift_type_label = {
                "morning": "Mañana",
                "afternoon": "Tarde", 
                "night": "Noche",
                "full_day": "Día Completo"
            }.get(shift_data.shift_type, shift_data.shift_type)
            
            date_str = shift_data.shift_date.strftime("%d/%m/%Y %H:%M")
            
            # Enviar email
            email_service = EmailService()
            email_service.send_shift_assigned_email(
                guard_email=assigned_guard.email,
                guard_name=assigned_guard.full_name,
                shift_date=shift_data.shift_date,
                shift_type=shift_data.shift_type,
                assigned_by=current_user.full_name
            )
            
            # Enviar notificación push
            if assigned_guard.fcm_token:
                fcm_service = FCMService()
                fcm_service.send_shift_assigned_notification(
                    device_token=assigned_guard.fcm_token,
                    guard_name=assigned_guard.full_name,
                    shift_date=date_str,
                    shift_type=shift_data.shift_type
                )
            
            print(f"📧 Notificación enviada a {assigned_guard.full_name} ({assigned_guard.email})")
            print(f"   Fecha: {date_str}, Tipo: {shift_type_label}")
    
    # Calcular shift_start y shift_end
    shift_start, shift_end = _calculate_shift_times(new_shift.shift_date, new_shift.shift_type)
    
    # Agregar nombre del guardia
    result = GuardShiftResponse(
        id=new_shift.id,
        condominium_id=new_shift.condominium_id,
        guard_id=new_shift.guard_id,
        guard_name=current_user.full_name,
        shift_date=new_shift.shift_date,
        shift_type=new_shift.shift_type,
        status=new_shift.status,
        notes=new_shift.notes,
        check_in_time=new_shift.check_in_time,
        check_out_time=new_shift.check_out_time,
        created_at=new_shift.created_at,
        updated_at=new_shift.updated_at,
        shift_start=shift_start,
        shift_end=shift_end
    )
    return result

@router.get("/available-guards")
def get_available_guards(
    shift_date: datetime = Query(..., description="Fecha y hora del turno a verificar"),
    shift_type: str = Query(..., description="Tipo de turno: morning, afternoon, night, full_day"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene lista de guardias disponibles para un turno específico"""
    if current_user.role not in ["admin", "super_admin", "owner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can check available guards"
        )
    
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    # Obtener todos los guardias del condominio
    guards = db.query(User).filter(
        User.condominium_id == current_user.condominium_id,
        User.role == "guard",
        User.is_active == True
    ).all()
    
    # Calcular rango del turno
    shift_start, shift_end = _calculate_shift_times(shift_date, shift_type)
    
    # Verificar qué guardias tienen conflictos
    available_guards = []
    for guard in guards:
        # Buscar turnos existentes del guardia
        existing_shifts = db.query(GuardShift).filter(
            GuardShift.guard_id == guard.id,
            GuardShift.condominium_id == current_user.condominium_id,
            GuardShift.status.in_(["scheduled", "active"])
        ).all()
        
        # Verificar solapamiento con cada turno existente
        conflicting_shift = None
        for existing in existing_shifts:
            existing_start, existing_end = _calculate_shift_times(existing.shift_date, existing.shift_type)
            # Verificar si hay solapamiento
            if (shift_start < existing_end and shift_end > existing_start):
                conflicting_shift = existing
                break
        
        available_guards.append({
            "id": str(guard.id),
            "name": guard.full_name,
            "email": guard.email,
            "available": conflicting_shift is None,
            "conflict_reason": f"Tiene turno el {conflicting_shift.shift_date.strftime('%Y-%m-%d %H:%M')}" if conflicting_shift else None
        })
    
    return {
        "shift_start": shift_start.isoformat(),
        "shift_end": shift_end.isoformat(),
        "guards": available_guards
    }

@router.get("/", response_model=List[GuardShiftResponse])
def get_guard_shifts(
    date_filter: Optional[date] = Query(None, alias="date"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )

    query = db.query(GuardShift).filter(
        GuardShift.condominium_id == current_user.condominium_id
    )

    # Si es guardia, solo ver sus propios turnos
    if current_user.role == "guard":
        query = query.filter(GuardShift.guard_id == current_user.id)

    # Filtrar por fecha si se proporciona
    if date_filter:
        start_of_day = datetime.combine(date_filter, datetime.min.time())
        end_of_day = datetime.combine(date_filter, datetime.max.time())
        query = query.filter(
            GuardShift.shift_date >= start_of_day,
            GuardShift.shift_date <= end_of_day
        )

    shifts = query.order_by(GuardShift.shift_date.asc()).all()
    
    # Agregar nombres de guardias y calcular shift_start/shift_end
    result = []
    for shift in shifts:
        guard = db.query(User).filter(User.id == shift.guard_id).first()
        shift_start, shift_end = _calculate_shift_times(shift.shift_date, shift.shift_type)
        result.append(GuardShiftResponse(
            id=shift.id,
            condominium_id=shift.condominium_id,
            guard_id=shift.guard_id,
            guard_name=guard.full_name if guard else None,
            shift_date=shift.shift_date,
            shift_type=shift.shift_type,
            status=shift.status,
            notes=shift.notes,
            check_in_time=shift.check_in_time,
            check_out_time=shift.check_out_time,
            created_at=shift.created_at,
            updated_at=shift.updated_at,
            shift_start=shift_start,
            shift_end=shift_end
        ))
    return result

@router.get("/current", response_model=Optional[GuardShiftResponse])
def get_current_guard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene el guardia que está de turno actualmente"""
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )

    now = datetime.utcnow()
    # Buscar turno activo (status='active' o 'scheduled' y la fecha coincide)
    current_shift = db.query(GuardShift).filter(
        GuardShift.condominium_id == current_user.condominium_id,
        GuardShift.shift_date <= now,
        GuardShift.status.in_(["scheduled", "active"]),
        # El turno debe estar en el rango de tiempo apropiado
        # (simplificado: asumimos que un turno dura 8 horas)
    ).order_by(GuardShift.shift_date.desc()).first()

    if not current_shift:
        return None

    guard = db.query(User).filter(User.id == current_shift.guard_id).first()
    shift_start, shift_end = _calculate_shift_times(current_shift.shift_date, current_shift.shift_type)
    return GuardShiftResponse(
        id=current_shift.id,
        condominium_id=current_shift.condominium_id,
        guard_id=current_shift.guard_id,
        guard_name=guard.full_name if guard else None,
        shift_date=current_shift.shift_date,
        shift_type=current_shift.shift_type,
        status=current_shift.status,
        notes=current_shift.notes,
        check_in_time=current_shift.check_in_time,
        check_out_time=current_shift.check_out_time,
        created_at=current_shift.created_at,
        updated_at=current_shift.updated_at,
        shift_start=shift_start,
        shift_end=shift_end
    )

@router.patch("/{shift_id}", response_model=GuardShiftResponse)
def update_guard_shift(
    shift_id: str,
    shift_update: GuardShiftUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from uuid import UUID
    try:
        shift_uuid = UUID(shift_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid shift ID format"
        )

    shift = db.query(GuardShift).filter(GuardShift.id == shift_uuid).first()
    if not shift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shift not found"
        )

    # Solo el guardia dueño del turno o un admin puede actualizarlo
    if current_user.role == "guard" and shift.guard_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own shifts"
        )

    if shift.condominium_id != current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    # Actualizar campos
    if shift_update.status:
        shift.status = shift_update.status
    if shift_update.check_in_time:
        shift.check_in_time = shift_update.check_in_time
        if shift.status == "scheduled":
            shift.status = "active"
    if shift_update.check_out_time:
        shift.check_out_time = shift_update.check_out_time
        if shift.status == "active":
            shift.status = "completed"
    if shift_update.notes:
        shift.notes = shift_update.notes

    db.commit()
    db.refresh(shift)

    guard = db.query(User).filter(User.id == shift.guard_id).first()
    shift_start, shift_end = _calculate_shift_times(shift.shift_date, shift.shift_type)
    return GuardShiftResponse(
        id=shift.id,
        condominium_id=shift.condominium_id,
        guard_id=shift.guard_id,
        guard_name=guard.full_name if guard else None,
        shift_date=shift.shift_date,
        shift_type=shift.shift_type,
        status=shift.status,
        notes=shift.notes,
        check_in_time=shift.check_in_time,
        check_out_time=shift.check_out_time,
        created_at=shift.created_at,
        updated_at=shift.updated_at,
        shift_start=shift_start,
        shift_end=shift_end
    )

