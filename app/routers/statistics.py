from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta, date
from app.db import get_db
from app.models import GuardShift, User
from app.auth import get_current_user

router = APIRouter()

@router.get("/attendance")
def get_attendance_statistics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    guard_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene estadísticas de asistencia"""
    if current_user.role not in ["admin", "super_admin", "owner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view statistics"
        )
    
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    # Fechas por defecto: último mes
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()
    
    # Query base
    query = db.query(GuardShift).filter(
        GuardShift.condominium_id == current_user.condominium_id,
        GuardShift.shift_date >= datetime.combine(start_date, datetime.min.time()),
        GuardShift.shift_date <= datetime.combine(end_date, datetime.max.time())
    )
    
    if guard_id:
        from uuid import UUID
        try:
            guard_uuid = UUID(guard_id)
            query = query.filter(GuardShift.guard_id == guard_uuid)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid guard ID format"
            )
    
    shifts = query.all()
    
    # Calcular estadísticas
    total_shifts = len(shifts)
    completed_shifts = len([s for s in shifts if s.status == "completed"])
    active_shifts = len([s for s in shifts if s.status == "active"])
    cancelled_shifts = len([s for s in shifts if s.status == "cancelled"])
    scheduled_shifts = len([s for s in shifts if s.status == "scheduled"])
    
    # Turnos con check-in
    shifts_with_checkin = len([s for s in shifts if s.check_in_time is not None])
    
    # Tasa de asistencia
    attendance_rate = (completed_shifts / total_shifts * 100) if total_shifts > 0 else 0
    
    # Estadísticas por guardia
    guard_stats = {}
    for shift in shifts:
        guard = db.query(User).filter(User.id == shift.guard_id).first()
        if not guard:
            continue
        
        guard_name = guard.full_name
        if guard_name not in guard_stats:
            guard_stats[guard_name] = {
                "total": 0,
                "completed": 0,
                "with_checkin": 0,
                "cancelled": 0
            }
        
        guard_stats[guard_name]["total"] += 1
        if shift.status == "completed":
            guard_stats[guard_name]["completed"] += 1
        if shift.check_in_time:
            guard_stats[guard_name]["with_checkin"] += 1
        if shift.status == "cancelled":
            guard_stats[guard_name]["cancelled"] += 1
    
    # Calcular tasas por guardia
    for guard_name in guard_stats:
        stats = guard_stats[guard_name]
        stats["attendance_rate"] = (stats["completed"] / stats["total"] * 100) if stats["total"] > 0 else 0
        stats["checkin_rate"] = (stats["with_checkin"] / stats["total"] * 100) if stats["total"] > 0 else 0
    
    # Estadísticas por tipo de turno
    shift_type_stats = {}
    for shift in shifts:
        shift_type = shift.shift_type
        if shift_type not in shift_type_stats:
            shift_type_stats[shift_type] = {"total": 0, "completed": 0}
        shift_type_stats[shift_type]["total"] += 1
        if shift.status == "completed":
            shift_type_stats[shift_type]["completed"] += 1
    
    return {
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        "overall": {
            "total_shifts": total_shifts,
            "completed": completed_shifts,
            "active": active_shifts,
            "scheduled": scheduled_shifts,
            "cancelled": cancelled_shifts,
            "with_checkin": shifts_with_checkin,
            "attendance_rate": round(attendance_rate, 2)
        },
        "by_guard": guard_stats,
        "by_shift_type": shift_type_stats
    }

@router.get("/compliance")
def get_compliance_statistics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene estadísticas de cumplimiento"""
    if current_user.role not in ["admin", "super_admin", "owner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view statistics"
        )
    
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    # Fechas por defecto: último mes
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()
    
    # Obtener turnos completados
    shifts = db.query(GuardShift).filter(
        GuardShift.condominium_id == current_user.condominium_id,
        GuardShift.status == "completed",
        GuardShift.shift_date >= datetime.combine(start_date, datetime.min.time()),
        GuardShift.shift_date <= datetime.combine(end_date, datetime.max.time())
    ).all()
    
    # Calcular cumplimiento
    on_time_checkins = 0
    late_checkins = 0
    no_checkin = 0
    
    for shift in shifts:
        if not shift.check_in_time:
            no_checkin += 1
            continue
        
        # Verificar si el check-in fue a tiempo (dentro de 15 minutos del inicio)
        from app.routers.guard_shifts import _calculate_shift_times
        shift_start, _ = _calculate_shift_times(shift.shift_date, shift.shift_type)
        
        time_diff = (shift.check_in_time - shift_start).total_seconds() / 60  # minutos
        
        if time_diff <= 15:
            on_time_checkins += 1
        else:
            late_checkins += 1
    
    total_completed = len(shifts)
    on_time_rate = (on_time_checkins / total_completed * 100) if total_completed > 0 else 0
    
    return {
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        "compliance": {
            "total_completed": total_completed,
            "on_time_checkins": on_time_checkins,
            "late_checkins": late_checkins,
            "no_checkin": no_checkin,
            "on_time_rate": round(on_time_rate, 2)
        }
    }

