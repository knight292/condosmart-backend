from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db import get_db
from app.models import Owner, Condominium, User
from app.schemas.owner import OwnerCreate, OwnerResponse, CondominiumSummary
from app.auth import get_current_user

router = APIRouter()

@router.get("/my-condominiums", response_model=List[CondominiumSummary])
def get_my_condominiums(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener todos los condominios del owner actual"""
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can access this endpoint"
        )
    
    if not current_user.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with an owner"
        )
    
    condominiums = db.query(Condominium).filter(
        Condominium.owner_id == current_user.owner_id
    ).all()
    
    result = []
    for condo in condominiums:
        # Contar usuarios, unidades, etc.
        users_count = db.query(User).filter(User.condominium_id == condo.id).count()
        result.append({
            "id": str(condo.id),
            "name": condo.name,
            "address": condo.address,
            "subscription_status": condo.subscription_status,
            "users_count": users_count,
            "created_at": condo.created_at.isoformat() if condo.created_at else None,
        })
    
    return result

@router.get("/", response_model=OwnerResponse)
def get_owner_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener información del owner actual"""
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can access this endpoint"
        )
    
    if not current_user.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with an owner"
        )
    
    owner = db.query(Owner).filter(Owner.id == current_user.owner_id).first()
    if not owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Owner not found"
        )
    
    return owner

