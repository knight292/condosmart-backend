from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db import get_db
from app.models import Reservation, User
from app.models.uuid_helper import USE_SQLITE
from app.schemas.reservation import ReservationCreate, ReservationResponse
from app.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
def create_reservation(
    reservation_data: ReservationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    if reservation_data.start_time >= reservation_data.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time"
        )
    
    # Convertir IDs a string si es SQLite
    condo_id = str(current_user.condominium_id) if (USE_SQLITE and current_user.condominium_id) else current_user.condominium_id
    user_id = str(current_user.id) if (USE_SQLITE and current_user.id) else current_user.id
    unit_id = None
    if reservation_data.unit_id:
        unit_id = str(reservation_data.unit_id) if USE_SQLITE else reservation_data.unit_id
    elif current_user.unit_id:
        unit_id = str(current_user.unit_id) if USE_SQLITE else current_user.unit_id
    
    conflicting = db.query(Reservation).filter(
        Reservation.condominium_id == condo_id,
        Reservation.facility_type == reservation_data.facility_type,
        Reservation.status == "confirmed",
        Reservation.start_time < reservation_data.end_time,
        Reservation.end_time > reservation_data.start_time
    ).first()
    
    if conflicting:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Time slot already reserved"
        )
    
    new_reservation = Reservation(
        condominium_id=condo_id,
        user_id=user_id,
        unit_id=unit_id,
        facility_type=reservation_data.facility_type,
        start_time=reservation_data.start_time,
        end_time=reservation_data.end_time,
        status="confirmed"
    )
    db.add(new_reservation)
    db.commit()
    db.refresh(new_reservation)
    return new_reservation

@router.get("/", response_model=List[ReservationResponse])
def get_reservations(
    facility_type: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Reservation)
    
    # Convertir IDs a string si es SQLite
    if USE_SQLITE:
        condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
        user_id = str(current_user.id) if current_user.id else None
    else:
        condo_id = current_user.condominium_id
        user_id = current_user.id
    
    if current_user.role == "resident":
        if user_id:
            query = query.filter(Reservation.user_id == user_id)
    elif current_user.role in ["admin", "super_admin"]:
        if condo_id:
            query = query.filter(Reservation.condominium_id == condo_id)
    
    if facility_type:
        query = query.filter(Reservation.facility_type == facility_type)
    
    reservations = query.order_by(Reservation.start_time.asc()).all()
    return reservations

@router.get("/availability")
def get_availability(
    facility_type: str,
    date: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    target_date = datetime.fromisoformat(date)
    start_of_day = target_date.replace(hour=0, minute=0, second=0)
    end_of_day = target_date.replace(hour=23, minute=59, second=59)
    
    # Convertir ID a string si es SQLite
    condo_id = str(current_user.condominium_id) if (USE_SQLITE and current_user.condominium_id) else current_user.condominium_id
    
    reservations = db.query(Reservation).filter(
        Reservation.condominium_id == condo_id,
        Reservation.facility_type == facility_type,
        Reservation.status == "confirmed",
        Reservation.start_time >= start_of_day,
        Reservation.start_time <= end_of_day
    ).all()
    
    booked_slots = []
    for res in reservations:
        booked_slots.append({
            "start": res.start_time.isoformat(),
            "end": res.end_time.isoformat()
        })
    
    return {"facility_type": facility_type, "date": date, "booked_slots": booked_slots}

@router.delete("/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_reservation(
    reservation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )
    
    # Convertir IDs a string si es SQLite para comparación
    if USE_SQLITE:
        user_id = str(current_user.id) if current_user.id else None
        reservation_user_id = str(reservation.user_id) if reservation.user_id else None
    else:
        user_id = current_user.id
        reservation_user_id = reservation.user_id
    
    if current_user.role == "resident" and reservation_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    time_until_start = (reservation.start_time - datetime.utcnow()).total_seconds() / 3600
    
    if time_until_start < 24:
        reservation.cancellation_fee = 100.00
    
    reservation.status = "cancelled"
    db.commit()
    return None

