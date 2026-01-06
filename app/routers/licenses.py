from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
import secrets
import string

from app.db import get_db
from app.models import License, Condominium, User
from app.models.uuid_helper import USE_SQLITE
from app.schemas.license import LicenseCreate, LicenseActivate, LicenseResponse, LicenseValidation
from app.auth import get_current_user

router = APIRouter()

# Configuración de paquetes
PACKAGE_CONFIG = {
    "basic": {
        "price": 40000,  # $40,000 MXN
        "max_units": 40,
        "max_users": None,  # Ilimitado
    },
    "intermediate": {
        "price": 60000,  # $60,000 MXN
        "max_units": 100,
        "max_users": None,
    },
    "premium": {
        "price": 80000,  # $80,000 MXN
        "max_units": None,  # Ilimitado
        "max_users": None,
    }
}

def generate_license_code() -> str:
    """Genera un código de licencia único"""
    # Formato: CS-XXXX-XXXX-XXXX (CondoSmart)
    chars = string.ascii_uppercase + string.digits
    segments = [
        ''.join(secrets.choice(chars) for _ in range(4))
        for _ in range(3)
    ]
    return f"CS-{'-'.join(segments)}"

@router.post("/generate", response_model=LicenseResponse, status_code=status.HTTP_201_CREATED)
def generate_license(
    license_data: LicenseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Genera un nuevo código de licencia.
    Solo super_admin puede generar licencias.
    """
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo super administradores pueden generar licencias"
        )
    
    # Validar tipo de paquete
    if license_data.package_type not in PACKAGE_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de paquete inválido. Opciones: {list(PACKAGE_CONFIG.keys())}"
        )
    
    config = PACKAGE_CONFIG[license_data.package_type]
    
    # Generar código único
    code = generate_license_code()
    while db.query(License).filter(License.code == code).first():
        code = generate_license_code()
    
    # Crear licencia
    new_license = License(
        code=code,
        package_type=license_data.package_type,
        max_units=license_data.max_units or config["max_units"],
        max_users=license_data.max_users or config["max_users"],
        purchase_price=license_data.purchase_price or config["price"],
        buyer_name=license_data.buyer_name,
        buyer_email=license_data.buyer_email,
        expires_at=license_data.expires_at,
        notes=license_data.notes,
        activated=False
    )
    
    db.add(new_license)
    db.commit()
    db.refresh(new_license)
    
    return new_license

@router.get("/validate", response_model=LicenseValidation)
def validate_license(
    code: str = Query(..., description="Código de licencia a validar"),
    db: Session = Depends(get_db)
):
    """
    Valida un código de licencia sin activarlo.
    Cualquiera puede validar (para verificar antes de activar).
    """
    license = db.query(License).filter(License.code == code.upper()).first()
    
    if not license:
        return LicenseValidation(
            valid=False,
            code=code,
            message="Código de licencia no encontrado"
        )
    
    # Verificar si está activada
    if license.activated:
        condominium = db.query(Condominium).filter(Condominium.license_id == license.id).first()
        return LicenseValidation(
            valid=True,
            code=code,
            package_type=license.package_type,
            activated=True,
            condominium_name=condominium.name if condominium else None,
            message="Licencia ya activada"
        )
    
    # Verificar expiración
    if license.expires_at and license.expires_at < datetime.utcnow():
        return LicenseValidation(
            valid=False,
            code=code,
            message="Licencia expirada"
        )
    
    return LicenseValidation(
        valid=True,
        code=code,
        package_type=license.package_type,
        activated=False,
        message="Licencia válida y disponible para activar"
    )

@router.post("/activate", response_model=LicenseResponse)
def activate_license(
    activation_data: LicenseActivate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Activa una licencia asociándola a un condominio.
    El usuario debe ser admin o super_admin.
    """
    license = db.query(License).filter(License.code == activation_data.code.upper()).first()
    
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Código de licencia no encontrado"
        )
    
    if license.activated:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta licencia ya fue activada"
        )
    
    # Verificar expiración
    if license.expires_at and license.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta licencia ha expirado"
        )
    
    # Convertir IDs a string si es SQLite
    if USE_SQLITE:
        condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
        user_id = str(current_user.id) if current_user.id else None
        license_id = str(license.id) if license.id else None
    else:
        condo_id = current_user.condominium_id
        user_id = current_user.id
        license_id = license.id
    
    # Crear o actualizar condominio
    if condo_id:
        # Si el usuario ya tiene un condominio, usar ese
        condominium = db.query(Condominium).filter(Condominium.id == condo_id).first()
        if condominium:
            condominium.license_id = license_id
            condominium.name = activation_data.condominium_name
            if activation_data.condominium_address:
                condominium.address = activation_data.condominium_address
    else:
        # Crear nuevo condominio
        condominium = Condominium(
            name=activation_data.condominium_name,
            address=activation_data.condominium_address,
            license_id=license_id,
            subscription_plan=license.package_type,
            subscription_status="active"
        )
        db.add(condominium)
        db.flush()
        
        # Asociar usuario al condominio
        if USE_SQLITE:
            current_user.condominium_id = str(condominium.id) if condominium.id else None
        else:
            current_user.condominium_id = condominium.id
        
        if current_user.role == "resident":
            current_user.role = "admin"  # El que activa se convierte en admin
    
    # Activar licencia
    license.activated = True
    license.activated_at = datetime.utcnow()
    license.activated_by = user_id
    # Asociar licencia al condominio (a través de license_id en condominium)
    condominium.license_id = license_id
    
    db.commit()
    db.refresh(license)
    
    return license

@router.get("/my-license", response_model=LicenseResponse)
def get_my_license(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene la licencia del condominio del usuario actual.
    """
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no está asociado a un condominio"
        )
    
    # Convertir condominium_id a string si es SQLite
    if USE_SQLITE:
        condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
    else:
        condo_id = current_user.condominium_id
    
    condominium = db.query(Condominium).filter(Condominium.id == condo_id).first()
    if not condominium or not condominium.license_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condominio no tiene licencia asociada"
        )
    
    # Convertir license_id para la query si es SQLite
    if USE_SQLITE:
        license_id = str(condominium.license_id) if condominium.license_id else None
    else:
        license_id = condominium.license_id
    
    license = db.query(License).filter(License.id == license_id).first() if license_id else None
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Licencia no encontrada"
        )
    
    return license

@router.get("/list", response_model=List[LicenseResponse])
def list_licenses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista todas las licencias (solo super_admin).
    """
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo super administradores pueden listar licencias"
        )
    
    licenses = db.query(License).order_by(License.created_at.desc()).all()
    return licenses

