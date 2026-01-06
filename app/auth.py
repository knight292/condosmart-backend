from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from uuid import UUID

from app.db import get_db
from app.models import User, Condominium

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    x_condominium_id: Optional[str] = Header(None)  # Header opcional para owners
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Convertir el string a UUID si es necesario
    # Para SQLite, los IDs son strings, para PostgreSQL son UUIDs
    from app.models.uuid_helper import USE_SQLITE
    
    try:
        if USE_SQLITE:
            # En SQLite, los IDs son strings, usar directamente
            user = db.query(User).filter(User.id == user_id).first()
        else:
            # En PostgreSQL, convertir a UUID
            user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
            user = db.query(User).filter(User.id == user_uuid).first()
    except (ValueError, TypeError):
        raise credentials_exception
    if user is None:
        raise credentials_exception
    
    # Si el usuario es owner y se especifica un condominio en el header,
    # verificar que el condominio pertenece al owner
    if user.role == "owner" and x_condominium_id:
        try:
            condo_uuid = UUID(x_condominium_id)
            condominium = db.query(Condominium).filter(
                Condominium.id == condo_uuid,
                Condominium.owner_id == user.owner_id
            ).first()
            
            if condominium:
                # Temporalmente asignar el condominium_id al usuario para esta sesión
                # Esto permite que los endpoints funcionen como si fuera admin de ese condominio
                user.condominium_id = condominium.id
        except (ValueError, TypeError):
            pass  # Si el UUID es inválido, continuar sin cambiar el condominium_id
    
    return user
