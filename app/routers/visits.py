from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import qrcode
import io
import base64
import uuid as uuid_lib

from app.db import get_db
from app.models import Visit, User
from app.models.uuid_helper import USE_SQLITE
from app.schemas.visit import VisitCreate, VisitResponse, VisitScan
from app.auth import get_current_user

router = APIRouter()

def generate_qr_code(data: str) -> str:
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"


@router.post("/generate", response_model=VisitResponse, status_code=status.HTTP_201_CREATED)
@router.post("/generate/", response_model=VisitResponse, status_code=status.HTTP_201_CREATED)
def generate_visit(
    visit_data: VisitCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    import logging
    logger = logging.getLogger(__name__)
    
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    # Log para debugging
    logger.info(f"🔍 Visit create - user_id: {current_user.id}, user_unit_id: {current_user.unit_id}, request_unit_id: {visit_data.unit_id}")
    
    # Usar unit_id del request si está disponible, sino del usuario
    unit_id_to_use = None
    if visit_data.unit_id:
        unit_id_to_use = str(visit_data.unit_id) if USE_SQLITE else visit_data.unit_id
        logger.info(f"✅ Using unit_id from request: {unit_id_to_use}")
    elif current_user.unit_id:
        unit_id_to_use = str(current_user.unit_id) if (USE_SQLITE and current_user.unit_id) else current_user.unit_id
        logger.info(f"✅ Using unit_id from user: {unit_id_to_use}")
    else:
        # Si no hay unit_id, intentar obtener la primera unidad del condominio del usuario
        from app.models import Unit
        condo_id = str(current_user.condominium_id) if (USE_SQLITE and current_user.condominium_id) else current_user.condominium_id
        first_unit = db.query(Unit).filter(Unit.condominium_id == condo_id).first()
        if first_unit:
            unit_id_to_use = str(first_unit.id) if USE_SQLITE else first_unit.id
            logger.info(f"✅ Using first unit from condominium: {unit_id_to_use}")
    
    if not unit_id_to_use:
        logger.error(f"❌ No unit_id available for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a unit or provide unit_id in request. Please contact an administrator to assign a unit."
        )
    
    qr_code_value = str(uuid_lib.uuid4())
    
    # Convertir IDs a string si es SQLite
    condo_id = str(current_user.condominium_id) if (USE_SQLITE and current_user.condominium_id) else current_user.condominium_id
    unit_id = unit_id_to_use
    
    new_visit = Visit(
        condominium_id=condo_id,
        unit_id=unit_id,
        resident_id=str(current_user.id) if (USE_SQLITE and current_user.id) else current_user.id,
        visitor_name=visit_data.visitor_name,
        visitor_phone=visit_data.visitor_phone,
        qr_code=qr_code_value,
        valid_until=visit_data.valid_until,
        status="pending"
    )
    db.add(new_visit)
    db.commit()
    db.refresh(new_visit)
    
    return new_visit

@router.get("/qr/{visit_id}")
def get_qr_code(
    visit_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Convertir IDs a string si es SQLite
    condo_id = str(current_user.condominium_id) if (USE_SQLITE and current_user.condominium_id) else current_user.condominium_id
    
    visit_query = db.query(Visit).filter(
        Visit.id == visit_id,
        Visit.condominium_id == condo_id
    )
    if current_user.role == "resident":
        user_id = str(current_user.id) if (USE_SQLITE and current_user.id) else current_user.id
        visit_query = visit_query.filter(Visit.resident_id == user_id)
    visit = visit_query.first()
    
    if not visit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visit not found"
        )
    
    qr_image = generate_qr_code(visit.qr_code)
    return {"qr_code": visit.qr_code, "qr_image": qr_image}

@router.post("/scan", response_model=VisitResponse)
def scan_visit(
    scan_data: VisitScan,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["guard", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only guards and admins can scan visits"
        )
    
    visit = db.query(Visit).filter(Visit.qr_code == scan_data.qr_code).first()
    
    if not visit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid QR code"
        )
    
    if visit.status == "checked_out":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Visit already checked out"
        )
    
    if datetime.utcnow() > visit.valid_until:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="QR code expired"
        )
    
    # Convertir ID a string si es SQLite
    user_id = str(current_user.id) if (USE_SQLITE and current_user.id) else current_user.id
    
    if visit.status == "pending":
        visit.status = "checked_in"
        visit.entry_time = datetime.utcnow()
        visit.scanned_by = user_id
    elif visit.status == "checked_in":
        visit.status = "checked_out"
        visit.exit_time = datetime.utcnow()
    
    db.commit()
    db.refresh(visit)
    return visit

@router.get("", response_model=List[VisitResponse])
@router.get("/", response_model=List[VisitResponse])
def get_visits(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Visit)
    
    # Convertir IDs a string si es SQLite
    if USE_SQLITE:
        condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
        unit_id = str(current_user.unit_id) if current_user.unit_id else None
    else:
        condo_id = current_user.condominium_id
        unit_id = current_user.unit_id
    
    if current_user.role == "resident":
        user_id = str(current_user.id) if (USE_SQLITE and current_user.id) else current_user.id
        query = query.filter(Visit.resident_id == user_id)
    elif current_user.role in ["admin", "guard"]:
        if condo_id:
            query = query.filter(Visit.condominium_id == condo_id)
    
    visits = query.order_by(Visit.created_at.desc()).all()
    return visits

