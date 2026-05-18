from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.db import get_db
from app.models import ShiftSwap, GuardShift, User
from app.models.uuid_helper import USE_SQLITE
from app.schemas.shift_swap import ShiftSwapCreate, ShiftSwapUpdate, ShiftSwapResponse
from app.auth import get_current_user
from app.deps.modules import require_module

router = APIRouter(dependencies=[Depends(require_module("guard_shifts"))])

@router.post("/", response_model=ShiftSwapResponse, status_code=status.HTTP_201_CREATED)
def create_swap_request(
    swap_data: ShiftSwapCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "guard":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only guards can request shift swaps"
        )
    
    # Convertir IDs a string si es SQLite
    if USE_SQLITE:
        shift_search_id = str(swap_data.shift_id) if swap_data.shift_id else None
        user_id = str(current_user.id) if current_user.id else None
        condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
    else:
        shift_search_id = swap_data.shift_id
        user_id = current_user.id
        condo_id = current_user.condominium_id
    
    # Verificar que el turno existe y pertenece al guardia
    shift = db.query(GuardShift).filter(GuardShift.id == shift_search_id).first()
    if not shift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shift not found"
        )
    
    # Convertir shift.guard_id para comparación
    if USE_SQLITE:
        shift_guard_id = str(shift.guard_id) if shift.guard_id else None
    else:
        shift_guard_id = shift.guard_id
    
    if shift_guard_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only request swaps for your own shifts"
        )
    
    if shift.status not in ["scheduled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only swap scheduled shifts"
        )
    
    # Verificar que no existe ya una solicitud pendiente para este turno
    existing_swap = db.query(ShiftSwap).filter(
        ShiftSwap.shift_id == shift_search_id,
        ShiftSwap.status == "pending"
    ).first()
    
    if existing_swap:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There is already a pending swap request for this shift"
        )
    
    # Si se especifica un guardia específico, verificar que existe
    if swap_data.requested_to:
        if USE_SQLITE:
            requested_to_id = str(swap_data.requested_to) if swap_data.requested_to else None
        else:
            requested_to_id = swap_data.requested_to
        
        target_guard = db.query(User).filter(
            User.id == requested_to_id,
            User.condominium_id == condo_id,
            User.role == "guard"
        ).first()
        if not target_guard:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target guard not found"
            )
    
    new_swap = ShiftSwap(
        shift_id=shift_search_id,
        requested_by=user_id,
        requested_to=str(swap_data.requested_to) if (USE_SQLITE and swap_data.requested_to) else swap_data.requested_to,
        reason=swap_data.reason,
        status="pending"
    )
    db.add(new_swap)
    db.commit()
    db.refresh(new_swap)
    
    # Obtener información del turno
    from app.routers.guard_shifts import _calculate_shift_times
    shift_start, shift_end = _calculate_shift_times(shift.shift_date, shift.shift_type)
    
    return ShiftSwapResponse(
        id=new_swap.id,
        shift_id=new_swap.shift_id,
        shift_info={
            "shift_date": shift.shift_date.isoformat(),
            "shift_type": shift.shift_type,
            "shift_start": shift_start.isoformat(),
            "shift_end": shift_end.isoformat()
        },
        requested_by=new_swap.requested_by,
        requester_name=current_user.full_name,
        requested_to=new_swap.requested_to,
        requested_to_name=target_guard.full_name if swap_data.requested_to and 'target_guard' in locals() else None,
        status=new_swap.status,
        reason=new_swap.reason,
        admin_response=new_swap.admin_response,
        responded_by=new_swap.responded_by,
        responder_name=None,
        created_at=new_swap.created_at,
        updated_at=new_swap.updated_at,
        responded_at=new_swap.responded_at
    )

@router.get("", response_model=List[ShiftSwapResponse])
@router.get("/", response_model=List[ShiftSwapResponse])
def get_swap_requests(
    status_filter: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    query = db.query(ShiftSwap)
    
    # Convertir IDs a string si es SQLite
    if USE_SQLITE:
        condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
        user_id = str(current_user.id) if current_user.id else None
    else:
        condo_id = current_user.condominium_id
        user_id = current_user.id
    
    if current_user.role == "guard":
        # Guardias ven sus propias solicitudes o solicitudes dirigidas a ellos
        query = query.filter(
            (ShiftSwap.requested_by == user_id) |
            (ShiftSwap.requested_to == user_id)
        )
    elif current_user.role in ["admin", "owner"]:
        # Admins ven todas las solicitudes del condominio
        # Obtener IDs de turnos del condominio
        condo_shifts = db.query(GuardShift.id).filter(
            GuardShift.condominium_id == condo_id
        ).all()
        shift_ids = [shift[0] for shift in condo_shifts]
        if shift_ids:
            query = query.filter(ShiftSwap.shift_id.in_(shift_ids))
        else:
            # Si no hay turnos, retornar lista vacía
            return []
    
    if status_filter:
        query = query.filter(ShiftSwap.status == status_filter)
    
    swaps = query.order_by(ShiftSwap.created_at.desc()).all()
    
    result = []
    for swap in swaps:
        # Convertir IDs para las queries si es SQLite
        if USE_SQLITE:
            shift_search_id = str(swap.shift_id) if swap.shift_id else None
            requester_search_id = str(swap.requested_by) if swap.requested_by else None
            responder_search_id = str(swap.responded_by) if swap.responded_by else None
            requested_to_search_id = str(swap.requested_to) if swap.requested_to else None
        else:
            shift_search_id = swap.shift_id
            requester_search_id = swap.requested_by
            responder_search_id = swap.responded_by
            requested_to_search_id = swap.requested_to
        
        shift = db.query(GuardShift).filter(GuardShift.id == shift_search_id).first() if shift_search_id else None
        requester = db.query(User).filter(User.id == requester_search_id).first() if requester_search_id else None
        responder = db.query(User).filter(User.id == responder_search_id).first() if responder_search_id else None
        
        requested_to_user = None
        if requested_to_search_id:
            requested_to_user = db.query(User).filter(User.id == requested_to_search_id).first()
        
        from app.routers.guard_shifts import _calculate_shift_times
        shift_start, shift_end = _calculate_shift_times(shift.shift_date, shift.shift_type) if shift else (None, None)
        
        result.append(ShiftSwapResponse(
            id=swap.id,
            shift_id=swap.shift_id,
            shift_info={
                "shift_date": shift.shift_date.isoformat() if shift else None,
                "shift_type": shift.shift_type if shift else None,
                "shift_start": shift_start.isoformat() if shift_start else None,
                "shift_end": shift_end.isoformat() if shift_end else None
            } if shift else None,
            requested_by=swap.requested_by,
            requester_name=requester.full_name if requester else None,
            requested_to=swap.requested_to,
            requested_to_name=requested_to_user.full_name if requested_to_user else None,
            status=swap.status,
            reason=swap.reason,
            admin_response=swap.admin_response,
            responded_by=swap.responded_by,
            responder_name=responder.full_name if responder else None,
            created_at=swap.created_at,
            updated_at=swap.updated_at,
            responded_at=swap.responded_at
        ))
    
    return result

@router.patch("/{swap_id}", response_model=ShiftSwapResponse)
def update_swap_request(
    swap_id: str,
    swap_update: ShiftSwapUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # En SQLite, los IDs son strings, usar directamente
    # En PostgreSQL, convertir a UUID
    if USE_SQLITE:
        swap_search_id = swap_id
    else:
        from uuid import UUID
        try:
            swap_search_id = UUID(swap_id) if isinstance(swap_id, str) else swap_id
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid swap ID format"
            )
    
    swap = db.query(ShiftSwap).filter(ShiftSwap.id == swap_search_id).first()
    if not swap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Swap request not found"
        )
    
    # Convertir IDs para las queries si es SQLite
    if USE_SQLITE:
        shift_search_id = str(swap.shift_id) if swap.shift_id else None
        condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
    else:
        shift_search_id = swap.shift_id
        condo_id = current_user.condominium_id
    
    shift = db.query(GuardShift).filter(GuardShift.id == shift_search_id).first() if shift_search_id else None
    if not shift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shift not found"
        )
    
    # Convertir shift.condominium_id para comparación
    if USE_SQLITE:
        shift_condo_id = str(shift.condominium_id) if shift.condominium_id else None
    else:
        shift_condo_id = shift.condominium_id
    
    if shift_condo_id != condo_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    # Solo admins pueden aprobar/rechazar, o el guardia puede cancelar su propia solicitud
    if swap_update.status in ["approved", "rejected"]:
        if current_user.role not in ["admin", "owner"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can approve or reject swap requests"
            )
        
        # Convertir user_id para asignación si es SQLite
        if USE_SQLITE:
            responded_by_id = str(current_user.id) if current_user.id else None
            requested_to_id = str(swap.requested_to) if swap.requested_to else None
            shift_guard_id = str(shift.guard_id) if shift.guard_id else None
        else:
            responded_by_id = current_user.id
            requested_to_id = swap.requested_to
            shift_guard_id = shift.guard_id
        
        swap.status = swap_update.status
        swap.responded_by = responded_by_id
        swap.responded_at = datetime.utcnow()
        swap.admin_response = swap_update.admin_response
        
        # Si se aprueba, cambiar el guardia del turno
        if swap_update.status == "approved":
            # Si hay un guardia específico solicitado, asignarle el turno
            if requested_to_id:
                new_guard = db.query(User).filter(User.id == requested_to_id).first()
                old_guard = db.query(User).filter(User.id == shift_guard_id).first()
                shift.guard_id = requested_to_id
                db.commit()
                
                # Notificar a ambos guardias
                if new_guard:
                    print(f"📧 Notificación: Intercambio aprobado - {new_guard.full_name} ahora tiene el turno")
                if old_guard:
                    print(f"📧 Notificación: Intercambio aprobado - {old_guard.full_name} ya no tiene el turno")
            # Si no hay guardia específico, el admin debe asignar manualmente o se puede dejar pendiente
            else:
                db.commit()
    
    elif swap_update.status == "cancelled":
        # Convertir IDs para comparación si es SQLite
        if USE_SQLITE:
            swap_requested_by = str(swap.requested_by) if swap.requested_by else None
            user_id = str(current_user.id) if current_user.id else None
        else:
            swap_requested_by = swap.requested_by
            user_id = current_user.id
        
        if current_user.role == "guard" and swap_requested_by != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cancel your own swap requests"
            )
        swap.status = "cancelled"
        db.commit()
    
    db.refresh(swap)
    
    # Construir respuesta - convertir IDs para las queries si es SQLite
    if USE_SQLITE:
        requester_search_id = str(swap.requested_by) if swap.requested_by else None
        responder_search_id = str(swap.responded_by) if swap.responded_by else None
        requested_to_search_id = str(swap.requested_to) if swap.requested_to else None
    else:
        requester_search_id = swap.requested_by
        responder_search_id = swap.responded_by
        requested_to_search_id = swap.requested_to
    
    requester = db.query(User).filter(User.id == requester_search_id).first() if requester_search_id else None
    responder = db.query(User).filter(User.id == responder_search_id).first() if responder_search_id else None
    requested_to_user = None
    if requested_to_search_id:
        requested_to_user = db.query(User).filter(User.id == requested_to_search_id).first()
    
    from app.routers.guard_shifts import _calculate_shift_times
    shift_start, shift_end = _calculate_shift_times(shift.shift_date, shift.shift_type)
    
    return ShiftSwapResponse(
        id=swap.id,
        shift_id=swap.shift_id,
        shift_info={
            "shift_date": shift.shift_date.isoformat(),
            "shift_type": shift.shift_type,
            "shift_start": shift_start.isoformat(),
            "shift_end": shift_end.isoformat()
        },
        requested_by=swap.requested_by,
        requester_name=requester.full_name if requester else None,
        requested_to=swap.requested_to,
        requested_to_name=requested_to_user.full_name if requested_to_user else None,
        status=swap.status,
        reason=swap.reason,
        admin_response=swap.admin_response,
        responded_by=swap.responded_by,
        responder_name=responder.full_name if responder else None,
        created_at=swap.created_at,
        updated_at=swap.updated_at,
        responded_at=swap.responded_at
    )

