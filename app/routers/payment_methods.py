from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.db import get_db
from app.models import PaymentMethod, User, Condominium
from app.models.uuid_helper import USE_SQLITE
from app.schemas.payment_method import PaymentMethodCreate, PaymentMethodUpdate, PaymentMethodResponse
from app.auth import get_current_user

router = APIRouter(prefix="/payment-methods", tags=["payment-methods"])

@router.get("", response_model=List[PaymentMethodResponse])
@router.get("/", response_model=List[PaymentMethodResponse])
def get_payment_methods(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener métodos de pago del condominio del usuario"""
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
    
    # Solo mostrar métodos activos para residentes, todos para administradores
    query = db.query(PaymentMethod).filter(
        PaymentMethod.condominium_id == condo_id
    )
    
    if current_user.role == "resident":
        query = query.filter(PaymentMethod.is_active == True)
    
    methods = query.order_by(PaymentMethod.method_type, PaymentMethod.name).all()
    return methods

@router.post("/", response_model=PaymentMethodResponse, status_code=status.HTTP_201_CREATED)
def create_payment_method(
    method_data: PaymentMethodCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear un nuevo método de pago (solo administradores)"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create payment methods"
        )
    
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
    
    # Verificar que el condominio existe
    condominium = db.query(Condominium).filter(
        Condominium.id == condo_id
    ).first()
    
    if not condominium:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condominium not found"
        )
    
    new_method = PaymentMethod(
        condominium_id=condo_id,
        method_type=method_data.method_type,
        name=method_data.name,
        account_number=method_data.account_number,
        bank_name=method_data.bank_name,
        clabe=method_data.clabe,
        account_holder=method_data.account_holder,
        gateway_name=method_data.gateway_name,
        gateway_config=method_data.gateway_config,
        requires_verification=method_data.requires_verification,
        instructions=method_data.instructions,
        is_active=method_data.is_active
    )
    
    db.add(new_method)
    db.commit()
    db.refresh(new_method)
    
    return new_method

@router.put("/{method_id}", response_model=PaymentMethodResponse)
def update_payment_method(
    method_id: UUID,
    method_data: PaymentMethodUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar un método de pago (solo administradores)"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update payment methods"
        )
    
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    # Convertir IDs a string si es SQLite
    if USE_SQLITE:
        condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
        method_search_id = str(method_id) if method_id else None
    else:
        condo_id = current_user.condominium_id
        method_search_id = method_id
    
    method = db.query(PaymentMethod).filter(
        PaymentMethod.id == method_search_id,
        PaymentMethod.condominium_id == condo_id
    ).first()
    
    if not method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment method not found"
        )
    
    # Actualizar campos
    update_data = method_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(method, field, value)
    
    db.commit()
    db.refresh(method)
    
    return method

@router.delete("/{method_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment_method(
    method_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar un método de pago (solo administradores)"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete payment methods"
        )
    
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    # Convertir IDs a string si es SQLite
    if USE_SQLITE:
        condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
        method_search_id = str(method_id) if method_id else None
    else:
        condo_id = current_user.condominium_id
        method_search_id = method_id
    
    method = db.query(PaymentMethod).filter(
        PaymentMethod.id == method_search_id,
        PaymentMethod.condominium_id == condo_id
    ).first()
    
    if not method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment method not found"
        )
    
    db.delete(method)
    db.commit()
    
    return None

