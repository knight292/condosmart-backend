from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.db import get_db
from app.models import ShiftSwap, GuardShift, User
from app.schemas.shift_swap import ShiftSwapCreate, ShiftSwapUpdate, ShiftSwapResponse
from app.auth import get_current_user
from uuid import UUID

router = APIRouter()

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
    
    # Verificar que el turno existe y pertenece al guardia
    shift = db.query(GuardShift).filter(GuardShift.id == swap_data.shift_id).first()
    if not shift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shift not found"
        )
    
    if shift.guard_id != current_user.id:
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
        ShiftSwap.shift_id == swap_data.shift_id,
        ShiftSwap.status == "pending"
    ).first()
    
    if existing_swap:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There is already a pending swap request for this shift"
        )
    
    # Si se especifica un guardia específico, verificar que existe
    if swap_data.requested_to:
        target_guard = db.query(User).filter(
            User.id == swap_data.requested_to,
            User.condominium_id == current_user.condominium_id,
            User.role == "guard"
        ).first()
        if not target_guard:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target guard not found"
            )
    
    new_swap = ShiftSwap(
        shift_id=swap_data.shift_id,
        requested_by=current_user.id,
        requested_to=swap_data.requested_to,
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
    
    if current_user.role == "guard":
        # Guardias ven sus propias solicitudes o solicitudes dirigidas a ellos
        query = query.filter(
            (ShiftSwap.requested_by == current_user.id) |
            (ShiftSwap.requested_to == current_user.id)
        )
    elif current_user.role in ["admin", "super_admin", "owner"]:
        # Admins ven todas las solicitudes del condominio
        # Obtener IDs de turnos del condominio
        condo_shifts = db.query(GuardShift.id).filter(
            GuardShift.condominium_id == current_user.condominium_id
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
        shift = db.query(GuardShift).filter(GuardShift.id == swap.shift_id).first()
        requester = db.query(User).filter(User.id == swap.requested_by).first()
        responder = db.query(User).filter(User.id == swap.responded_by).first() if swap.responded_by else None
        
        requested_to_user = None
        if swap.requested_to:
            requested_to_user = db.query(User).filter(User.id == swap.requested_to).first()
        
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
    try:
        swap_uuid = UUID(swap_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid swap ID format"
        )
    
    swap = db.query(ShiftSwap).filter(ShiftSwap.id == swap_uuid).first()
    if not swap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Swap request not found"
        )
    
    shift = db.query(GuardShift).filter(GuardShift.id == swap.shift_id).first()
    if not shift or shift.condominium_id != current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    # Solo admins pueden aprobar/rechazar, o el guardia puede cancelar su propia solicitud
    if swap_update.status in ["approved", "rejected"]:
        if current_user.role not in ["admin", "super_admin", "owner"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can approve or reject swap requests"
            )
        
        swap.status = swap_update.status
        swap.responded_by = current_user.id
        swap.responded_at = datetime.utcnow()
        swap.admin_response = swap_update.admin_response
        
        # Si se aprueba, cambiar el guardia del turno
        if swap_update.status == "approved":
            # Si hay un guardia específico solicitado, asignarle el turno
            if swap.requested_to:
                new_guard = db.query(User).filter(User.id == swap.requested_to).first()
                old_guard = db.query(User).filter(User.id == shift.guard_id).first()
                shift.guard_id = swap.requested_to
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
        if current_user.role == "guard" and swap.requested_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cancel your own swap requests"
            )
        swap.status = "cancelled"
        db.commit()
    
    db.refresh(swap)
    
    # Construir respuesta
    requester = db.query(User).filter(User.id == swap.requested_by).first()
    responder = db.query(User).filter(User.id == swap.responded_by).first() if swap.responded_by else None
    requested_to_user = None
    if swap.requested_to:
        requested_to_user = db.query(User).filter(User.id == swap.requested_to).first()
    
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

