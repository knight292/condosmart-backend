from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User, Condominium
from app.models.uuid_helper import USE_SQLITE
from app.schemas.auth import Token, UserCreate, UserResponse
from app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from datetime import timedelta

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@router.post("/register/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Verificar si el usuario ya existe
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Convertir IDs a string si es SQLite
    condo_id = None
    unit_id = None
    
    if user_data.condominium_id:
        condo_id = str(user_data.condominium_id) if (USE_SQLITE and user_data.condominium_id) else user_data.condominium_id
        
        # Verificar que el condominio existe y tiene licencia activa
        if USE_SQLITE:
            condo_search_id = str(user_data.condominium_id) if user_data.condominium_id else None
        else:
            condo_search_id = user_data.condominium_id
        
        condominium = db.query(Condominium).filter(Condominium.id == condo_search_id).first() if condo_search_id else None
        if not condominium:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Condominium not found"
            )
        
        # Verificar que el condominio tiene licencia activa
        if not condominium.license_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El condominio no tiene una licencia activa"
            )
    
    if user_data.unit_id:
        unit_id = str(user_data.unit_id) if (USE_SQLITE and user_data.unit_id) else user_data.unit_id
    
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        full_name=user_data.full_name,
        phone=user_data.phone,
        role=user_data.role or "resident",
        condominium_id=condo_id,
        unit_id=unit_id,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    print(f"🔍 Intentando login para email: {form_data.username}")
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user:
        print(f"❌ Usuario no encontrado: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print(f"✅ Usuario encontrado: {user.email}, ID: {user.id}, Tipo ID: {type(user.id)}")
    print(f"🔍 Verificando contraseña...")
    print(f"🔍 Password hash en DB: {user.password_hash[:50] if user.password_hash else 'None'}...")
    
    password_valid = verify_password(form_data.password, user.password_hash)
    print(f"🔍 Resultado verificación contraseña: {password_valid}")
    
    if not password_valid:
        print(f"❌ Contraseña incorrecta para: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Crear token con información del usuario
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/switch-condominium/{condominium_id}")
def switch_condominium(
    condominium_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Permite a un owner cambiar el condominio activo"""
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can switch condominiums"
        )
    
    if not current_user.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with an owner"
        )
    
    # Verificar que el condominio pertenece al owner
    from uuid import UUID
    try:
        condo_uuid = UUID(condominium_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid condominium ID format"
        )
    
    condominium = db.query(Condominium).filter(
        Condominium.id == condo_uuid,
        Condominium.owner_id == current_user.owner_id
    ).first()
    
    if not condominium:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condominium not found or does not belong to this owner"
        )
    
    # Retornar información del condominio seleccionado
    return {
        "condominium_id": str(condominium.id),
        "condominium_name": condominium.name,
        "message": f"Switched to condominium: {condominium.name}"
    }
