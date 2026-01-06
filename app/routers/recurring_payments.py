from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime, timedelta
from uuid import UUID
import logging

from app.db import get_db
from app.models import RecurringPayment, User, Payment
from app.models.uuid_helper import USE_SQLITE
from app.schemas.recurring_payment import (
    RecurringPaymentCreate, RecurringPaymentUpdate, RecurringPaymentResponse
)
from app.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

def calculate_next_generation(current_date: date, frequency: str, day_of_month: int) -> date:
    """Calcula la próxima fecha de generación"""
    if frequency == "monthly":
        # Próximo mes, mismo día
        if current_date.month == 12:
            next_date = date(current_date.year + 1, 1, min(day_of_month, 28))
        else:
            next_month = current_date.month + 1
            # Ajustar día si es mayor al último día del mes
            try:
                next_date = date(current_date.year, next_month, day_of_month)
            except ValueError:
                # Si el día no existe (ej: 31 de febrero), usar el último día del mes
                from calendar import monthrange
                last_day = monthrange(current_date.year, next_month)[1]
                next_date = date(current_date.year, next_month, min(day_of_month, last_day))
    elif frequency == "quarterly":
        # Cada 3 meses
        next_month = current_date.month + 3
        if next_month > 12:
            next_date = date(current_date.year + 1, next_month - 12, min(day_of_month, 28))
        else:
            try:
                next_date = date(current_date.year, next_month, day_of_month)
            except ValueError:
                from calendar import monthrange
                last_day = monthrange(current_date.year, next_month)[1]
                next_date = date(current_date.year, next_month, min(day_of_month, last_day))
    elif frequency == "yearly":
        # Cada año
        try:
            next_date = date(current_date.year + 1, current_date.month, day_of_month)
        except ValueError:
            from calendar import monthrange
            last_day = monthrange(current_date.year + 1, current_date.month)[1]
            next_date = date(current_date.year + 1, current_date.month, min(day_of_month, last_day))
    else:
        raise ValueError(f"Frecuencia no válida: {frequency}")
    
    return next_date

@router.post("", response_model=RecurringPaymentResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=RecurringPaymentResponse, status_code=status.HTTP_201_CREATED)
def create_recurring_payment(
    payment_data: RecurringPaymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear un pago recurrente"""
    if current_user.role not in ["admin", "super_admin", "owner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden crear pagos recurrentes"
        )
    
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes pertenecer a un condominio"
        )
    
    # Validar frecuencia
    if payment_data.frequency not in ["monthly", "quarterly", "yearly"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Frecuencia debe ser: monthly, quarterly o yearly"
        )
    
    # Validar día del mes
    if payment_data.day_of_month < 1 or payment_data.day_of_month > 31:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Día del mes debe estar entre 1 y 31"
        )
    
    # Si se especifica user_id, verificar que existe y pertenece al condominio
    user_id_value = None
    if payment_data.user_id:
        if USE_SQLITE:
            user_id_value = str(payment_data.user_id) if payment_data.user_id else None
        else:
            user_id_value = payment_data.user_id
        
        target_user = db.query(User).filter(User.id == user_id_value).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Verificar que pertenece al mismo condominio
        if USE_SQLITE:
            target_condo_id = str(target_user.condominium_id) if target_user.condominium_id else None
            user_condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
        else:
            target_condo_id = target_user.condominium_id
            user_condo_id = current_user.condominium_id
        
        if target_condo_id != user_condo_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El usuario debe pertenecer a tu condominio"
            )
    
    # Convertir IDs
    condo_id = str(current_user.condominium_id) if (USE_SQLITE and current_user.condominium_id) else current_user.condominium_id
    creator_id = str(current_user.id) if (USE_SQLITE and current_user.id) else current_user.id
    
    # Calcular próxima generación
    next_gen = calculate_next_generation(payment_data.start_date, payment_data.frequency, payment_data.day_of_month)
    
    new_recurring = RecurringPayment(
        condominium_id=condo_id,
        user_id=user_id_value,
        amount=payment_data.amount,
        currency=payment_data.currency,
        description=payment_data.description,
        frequency=payment_data.frequency,
        day_of_month=payment_data.day_of_month,
        start_date=payment_data.start_date,
        end_date=payment_data.end_date,
        is_active=True,
        next_generation=next_gen,
        created_by=creator_id
    )
    
    db.add(new_recurring)
    db.commit()
    db.refresh(new_recurring)
    
    # Obtener información adicional
    user_name = None
    if new_recurring.user_id:
        user = db.query(User).filter(User.id == new_recurring.user_id).first()
        user_name = user.full_name if user else None
    
    creator = db.query(User).filter(User.id == creator_id).first()
    creator_name = creator.full_name if creator else None
    
    return {
        "id": new_recurring.id,
        "condominium_id": new_recurring.condominium_id,
        "user_id": new_recurring.user_id,
        "amount": new_recurring.amount,
        "currency": new_recurring.currency,
        "description": new_recurring.description,
        "frequency": new_recurring.frequency,
        "day_of_month": new_recurring.day_of_month,
        "start_date": new_recurring.start_date,
        "end_date": new_recurring.end_date,
        "is_active": new_recurring.is_active,
        "last_generated": new_recurring.last_generated,
        "next_generation": new_recurring.next_generation,
        "created_by": new_recurring.created_by,
        "created_at": new_recurring.created_at,
        "updated_at": new_recurring.updated_at,
        "user_name": user_name,
        "creator_name": creator_name,
    }

@router.get("", response_model=List[RecurringPaymentResponse])
@router.get("/", response_model=List[RecurringPaymentResponse])
def get_recurring_payments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener todos los pagos recurrentes del condominio"""
    if current_user.role not in ["admin", "super_admin", "owner", "resident"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver pagos recurrentes"
        )
    
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes pertenecer a un condominio"
        )
    
    condo_id = str(current_user.condominium_id) if (USE_SQLITE and current_user.condominium_id) else current_user.condominium_id
    
    query = db.query(RecurringPayment).filter(RecurringPayment.condominium_id == condo_id)
    
    # Si es residente, solo ver los que le corresponden
    if current_user.role == "resident":
        user_id = str(current_user.id) if (USE_SQLITE and current_user.id) else current_user.id
        query = query.filter(
            (RecurringPayment.user_id == user_id) | (RecurringPayment.user_id == None)
        )
    
    recurring_payments = query.order_by(RecurringPayment.created_at.desc()).all()
    
    result = []
    for rp in recurring_payments:
        user_name = None
        if rp.user_id:
            user = db.query(User).filter(User.id == rp.user_id).first()
            user_name = user.full_name if user else None
        
        creator = db.query(User).filter(User.id == rp.created_by).first()
        creator_name = creator.full_name if creator else None
        
        result.append({
            "id": rp.id,
            "condominium_id": rp.condominium_id,
            "user_id": rp.user_id,
            "amount": rp.amount,
            "currency": rp.currency,
            "description": rp.description,
            "frequency": rp.frequency,
            "day_of_month": rp.day_of_month,
            "start_date": rp.start_date,
            "end_date": rp.end_date,
            "is_active": rp.is_active,
            "last_generated": rp.last_generated,
            "next_generation": rp.next_generation,
            "created_by": rp.created_by,
            "created_at": rp.created_at,
            "updated_at": rp.updated_at,
            "user_name": user_name,
            "creator_name": creator_name,
        })
    
    return result

@router.patch("/{recurring_id}", response_model=RecurringPaymentResponse)
def update_recurring_payment(
    recurring_id: str,
    payment_update: RecurringPaymentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar un pago recurrente"""
    if current_user.role not in ["admin", "super_admin", "owner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden actualizar pagos recurrentes"
        )
    
    recurring = db.query(RecurringPayment).filter(RecurringPayment.id == recurring_id).first()
    if not recurring:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pago recurrente no encontrado"
        )
    
    # Verificar que pertenece al mismo condominio
    if USE_SQLITE:
        recurring_condo_id = str(recurring.condominium_id) if recurring.condominium_id else None
        user_condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
    else:
        recurring_condo_id = recurring.condominium_id
        user_condo_id = current_user.condominium_id
    
    if recurring_condo_id != user_condo_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puedes actualizar pagos recurrentes de tu condominio"
        )
    
    # Actualizar campos
    if payment_update.amount is not None:
        recurring.amount = payment_update.amount
    if payment_update.currency is not None:
        recurring.currency = payment_update.currency
    if payment_update.description is not None:
        recurring.description = payment_update.description
    if payment_update.frequency is not None:
        recurring.frequency = payment_update.frequency
    if payment_update.day_of_month is not None:
        recurring.day_of_month = payment_update.day_of_month
    if payment_update.end_date is not None:
        recurring.end_date = payment_update.end_date
    if payment_update.is_active is not None:
        recurring.is_active = payment_update.is_active
    
    # Recalcular próxima generación si cambió frecuencia o día
    if payment_update.frequency is not None or payment_update.day_of_month is not None:
        base_date = recurring.last_generated if recurring.last_generated else recurring.start_date
        recurring.next_generation = calculate_next_generation(
            base_date, recurring.frequency, recurring.day_of_month
        )
    
    db.commit()
    db.refresh(recurring)
    
    # Obtener información adicional
    user_name = None
    if recurring.user_id:
        user = db.query(User).filter(User.id == recurring.user_id).first()
        user_name = user.full_name if user else None
    
    creator = db.query(User).filter(User.id == recurring.created_by).first()
    creator_name = creator.full_name if creator else None
    
    return {
        "id": recurring.id,
        "condominium_id": recurring.condominium_id,
        "user_id": recurring.user_id,
        "amount": recurring.amount,
        "currency": recurring.currency,
        "description": recurring.description,
        "frequency": recurring.frequency,
        "day_of_month": recurring.day_of_month,
        "start_date": recurring.start_date,
        "end_date": recurring.end_date,
        "is_active": recurring.is_active,
        "last_generated": recurring.last_generated,
        "next_generation": recurring.next_generation,
        "created_by": recurring.created_by,
        "created_at": recurring.created_at,
        "updated_at": recurring.updated_at,
        "user_name": user_name,
        "creator_name": creator_name,
    }

@router.delete("/{recurring_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recurring_payment(
    recurring_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar un pago recurrente"""
    if current_user.role not in ["admin", "super_admin", "owner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden eliminar pagos recurrentes"
        )
    
    recurring = db.query(RecurringPayment).filter(RecurringPayment.id == recurring_id).first()
    if not recurring:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pago recurrente no encontrado"
        )
    
    # Verificar que pertenece al mismo condominio
    if USE_SQLITE:
        recurring_condo_id = str(recurring.condominium_id) if recurring.condominium_id else None
        user_condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
    else:
        recurring_condo_id = recurring.condominium_id
        user_condo_id = current_user.condominium_id
    
    if recurring_condo_id != user_condo_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puedes eliminar pagos recurrentes de tu condominio"
        )
    
    db.delete(recurring)
    db.commit()

@router.post("/{recurring_id}/generate", status_code=status.HTTP_200_OK)
def generate_payments_from_recurring(
    recurring_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generar pagos desde un pago recurrente (ejecutar manualmente)"""
    if current_user.role not in ["admin", "super_admin", "owner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden generar pagos"
        )
    
    recurring = db.query(RecurringPayment).filter(RecurringPayment.id == recurring_id).first()
    if not recurring:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pago recurrente no encontrado"
        )
    
    if not recurring.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El pago recurrente está inactivo"
        )
    
    # Verificar que pertenece al mismo condominio
    if USE_SQLITE:
        recurring_condo_id = str(recurring.condominium_id) if recurring.condominium_id else None
        user_condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
    else:
        recurring_condo_id = recurring.condominium_id
        user_condo_id = current_user.condominium_id
    
    if recurring_condo_id != user_condo_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puedes generar pagos de tu condominio"
        )
    
    today = date.today()
    
    # Calcular fecha de vencimiento (próximo mes)
    if today.month == 12:
        due_date = date(today.year + 1, 1, recurring.day_of_month)
    else:
        try:
            due_date = date(today.year, today.month + 1, recurring.day_of_month)
        except ValueError:
            from calendar import monthrange
            last_day = monthrange(today.year, today.month + 1)[1]
            due_date = date(today.year, today.month + 1, min(recurring.day_of_month, last_day))
    
    # Obtener usuarios objetivo
    if recurring.user_id:
        # Pago para un usuario específico
        users = [db.query(User).filter(User.id == recurring.user_id).first()]
    else:
        # Pago para todos los residentes del condominio
        users = db.query(User).filter(
            User.condominium_id == recurring_condo_id,
            User.role == "resident"
        ).all()
    
    created_payments = []
    for user in users:
        if not user:
            continue
        
        # Verificar si ya existe un pago pendiente para este usuario con esta descripción y fecha
        user_id_value = str(user.id) if (USE_SQLITE and user.id) else user.id
        existing_payment = db.query(Payment).filter(
            Payment.user_id == user_id_value,
            Payment.condominium_id == recurring_condo_id,
            Payment.status == "pending",
            Payment.due_date == due_date
        ).first()
        
        if existing_payment:
            logger.info(f"Ya existe un pago pendiente para {user.email} con fecha {due_date}")
            continue
        
        # Crear nuevo pago
        new_payment = Payment(
            user_id=user_id_value,
            condominium_id=recurring_condo_id,
            amount=recurring.amount,
            currency=recurring.currency,
            due_date=due_date,
            status="pending"
        )
        db.add(new_payment)
        created_payments.append(new_payment)
    
    # Actualizar pago recurrente
    recurring.last_generated = today
    recurring.next_generation = calculate_next_generation(
        today, recurring.frequency, recurring.day_of_month
    )
    
    db.commit()
    
    return {
        "message": f"Se generaron {len(created_payments)} pagos",
        "recurring_payment_id": recurring.id,
        "payments_created": len(created_payments),
        "next_generation": recurring.next_generation
    }
