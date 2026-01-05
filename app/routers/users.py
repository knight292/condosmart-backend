from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.db import get_db
from app.models import User, Condominium, Unit
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.auth import get_current_user, get_password_hash

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
def get_users(
    role_filter: Optional[str] = Query(None, alias="role"),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener lista de usuarios del condominio"""
    # Permitir a admins, super_admins, owners y guards (para búsqueda de residentes)
    if current_user.role not in ["admin", "super_admin", "owner", "guard"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins, owners, or guards can view users"
        )
    
    # Determinar condominium_id a usar
    condominium_id = current_user.condominium_id
    if current_user.role == "owner":
        # Para owners, usar el condominio del header si está presente
        # Por ahora, usar el condominium_id del usuario si existe
        pass
    
    if not condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    query = db.query(User).filter(User.condominium_id == condominium_id)
    
    if role_filter:
        query = query.filter(User.role == role_filter)
    
    if search:
        query = query.filter(
            (User.email.ilike(f"%{search}%")) |
            (User.full_name.ilike(f"%{search}%"))
        )
    
    users = query.order_by(User.created_at.desc()).all()
    return users

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear un nuevo usuario (solo admins)"""
    if current_user.role not in ["admin", "super_admin", "owner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create users"
        )
    
    # Verificar si el email ya existe
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Determinar condominium_id
    condominium_id = user_data.condominium_id or current_user.condominium_id
    
    if not condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Condominium ID is required"
        )
    
    # Verificar que el condominio existe
    condominium = db.query(Condominium).filter(Condominium.id == condominium_id).first()
    if not condominium:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condominium not found"
        )
    
    # Si es owner, verificar que el condominio le pertenece
    if current_user.role == "owner" and condominium.owner_id != current_user.owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create users for your own condominiums"
        )
    
    # Verificar unidad si se especifica
    if user_data.unit_id:
        unit = db.query(Unit).filter(
            Unit.id == user_data.unit_id,
            Unit.condominium_id == condominium_id
        ).first()
        if not unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found or does not belong to this condominium"
            )
    
    new_user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        phone=user_data.phone,
        role=user_data.role,
        condominium_id=condominium_id,
        unit_id=user_data.unit_id,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar un usuario (solo admins)"""
    if current_user.role not in ["admin", "super_admin", "owner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update users"
        )
    
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verificar que el usuario pertenece al mismo condominio
    if user.condominium_id != current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update users from your condominium"
        )
    
    # Actualizar campos
    if user_update.full_name:
        user.full_name = user_update.full_name
    if user_update.phone is not None:
        user.phone = user_update.phone
    if user_update.email:
        user.email = user_update.email
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    if user_update.fcm_token is not None:
        user.fcm_token = user_update.fcm_token
    
    db.commit()
    db.refresh(user)
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar un usuario (solo admins)"""
    if current_user.role not in ["admin", "super_admin", "owner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete users"
        )
    
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verificar que el usuario pertenece al mismo condominio
    if user.condominium_id != current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete users from your condominium"
        )
    
    # No permitir eliminar el propio usuario
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account"
        )
    
    db.delete(user)
    db.commit()
    return None

