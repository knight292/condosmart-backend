from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.db import get_db
from app.models import User, Condominium, Unit
from app.models.uuid_helper import USE_SQLITE
from app.schemas.user import UserCreate, UserResponse, UserUpdate, FcmTokenUpdate
from app.auth import get_current_user, get_password_hash

router = APIRouter()

@router.get("", response_model=List[UserResponse])
@router.get("/", response_model=List[UserResponse])
def get_users(
    role_filter: Optional[str] = Query(None, alias="role"),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener lista de usuarios del condominio"""
    # Super_admin no debe acceder a usuarios de condominios específicos
    if current_user.role == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin cannot access condominium users"
        )
    
    # Permitir a admins, owners y guards (para búsqueda de residentes)
    if current_user.role not in ["admin", "owner", "guard"]:
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
    
    # Convertir condominium_id a string si es SQLite
    if USE_SQLITE:
        condo_id = str(condominium_id) if condominium_id else None
    else:
        condo_id = condominium_id
    
    query = db.query(User).filter(User.condominium_id == condo_id)
    
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
    # Super_admin no debe crear usuarios de condominios específicos
    if current_user.role == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin cannot create condominium users"
        )
    
    if current_user.role not in ["admin", "owner"]:
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
    
    # Convertir condominium_id a string si es SQLite para la query
    if USE_SQLITE:
        condo_search_id = str(condominium_id) if condominium_id else None
    else:
        condo_search_id = condominium_id
    
    # Verificar que el condominio existe
    condominium = db.query(Condominium).filter(Condominium.id == condo_search_id).first()
    if not condominium:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condominium not found"
        )
    
    # Verificar que el condominio tiene una licencia activa
    if not condominium.license_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El condominio no tiene una licencia activa. Debe activar una licencia antes de crear usuarios."
        )
    
    # Verificar que la licencia está activada
    from app.models import License
    if USE_SQLITE:
        license_search_id = str(condominium.license_id) if condominium.license_id else None
    else:
        license_search_id = condominium.license_id
    
    license = db.query(License).filter(License.id == license_search_id).first() if license_search_id else None
    if not license or not license.activated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La licencia del condominio no está activa. Debe activar la licencia antes de crear usuarios."
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
    
    # Convertir condominium_id a string si es SQLite para asignación
    if USE_SQLITE:
        condo_id_value = str(condominium_id) if condominium_id else None
        unit_id_value = str(user_data.unit_id) if user_data.unit_id else None
    else:
        condo_id_value = condominium_id
        unit_id_value = user_data.unit_id
    
    new_user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        phone=user_data.phone,
        role=user_data.role,
        condominium_id=condo_id_value,
        unit_id=unit_id_value,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.patch("/{user_id}", response_model=UserResponse)
@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar un usuario (solo admins)"""
    # Super_admin no debe crear usuarios de condominios específicos
    if current_user.role == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin cannot create condominium users"
        )
    
    if current_user.role not in ["admin", "owner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update users"
        )
    
    # Convertir user_id para la búsqueda
    if USE_SQLITE:
        user_search_id = str(user_id) if user_id else None
    else:
        try:
            user_search_id = UUID(user_id) if isinstance(user_id, str) else user_id
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format"
            )
    
    user = db.query(User).filter(User.id == user_search_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verificar que el usuario pertenece al mismo condominio (manejar SQLite)
    if USE_SQLITE:
        user_condo_id = str(user.condominium_id) if user.condominium_id else None
        current_condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
    else:
        user_condo_id = user.condominium_id
        current_condo_id = current_user.condominium_id
    
    if user_condo_id != current_condo_id:
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
        # Verificar que el email no esté en uso por otro usuario
        existing_user = db.query(User).filter(
            User.email == user_update.email,
            User.id != user_search_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use by another user"
            )
        user.email = user_update.email
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    if user_update.fcm_token is not None:
        user.fcm_token = user_update.fcm_token
    if user_update.role is not None:
        # Solo super_admin puede cambiar roles
        if current_user.role != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super_admin can change user roles"
            )
        # No permitir cambiar el rol de super_admin
        if user.role == "super_admin" and user_update.role != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot change super_admin role"
            )
        user.role = user_update.role
    if user_update.unit_id is not None:
        # Verificar que la unidad existe y pertenece al condominio
        if user_update.unit_id:
            if USE_SQLITE:
                unit_search_id = str(user_update.unit_id) if user_update.unit_id else None
            else:
                unit_search_id = user_update.unit_id
            
            unit = db.query(Unit).filter(Unit.id == unit_search_id).first()
            if not unit:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Unit not found"
                )
            
            # Verificar que la unidad pertenece al mismo condominio
            if USE_SQLITE:
                unit_condo_id = str(unit.condominium_id) if unit.condominium_id else None
            else:
                unit_condo_id = unit.condominium_id
            
            if unit_condo_id != current_condo_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Unit does not belong to your condominium"
                )
            
            if USE_SQLITE:
                user.unit_id = str(user_update.unit_id) if user_update.unit_id else None
            else:
                user.unit_id = user_update.unit_id
        else:
            user.unit_id = None
    
    db.commit()
    db.refresh(user)
    return user


@router.patch("/me/fcm-token", response_model=UserResponse)
def update_my_fcm_token(
    token_update: FcmTokenUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar el FCM token del usuario actual"""
    current_user.fcm_token = token_update.fcm_token
    db.commit()
    db.refresh(current_user)
    return current_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar un usuario (solo admins)"""
    # Super_admin no debe crear usuarios de condominios específicos
    if current_user.role == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin cannot create condominium users"
        )
    
    if current_user.role not in ["admin", "owner"]:
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

