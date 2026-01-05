from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta
from uuid import UUID

from app.db import get_db
from app.models import Contract, User, Announcement
from app.schemas.contract import ContractCreate, ContractUpdate, ContractResponse
from app.auth import get_current_user

router = APIRouter()

def calculate_renewal_date(end_date: date) -> date:
    """Calcula la fecha de renovación (1 mes antes de end_date)"""
    if end_date.month == 1:
        renewal_date = date(end_date.year - 1, 12, end_date.day)
    else:
        renewal_date = date(end_date.year, end_date.month - 1, end_date.day)
    return renewal_date

@router.post("/", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
def create_contract(
    contract_data: ContractCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create contracts"
        )
    
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    renewal_date = calculate_renewal_date(contract_data.end_date)
    
    new_contract = Contract(
        condominium_id=current_user.condominium_id,
        created_by=current_user.id,
        title=contract_data.title,
        description=contract_data.description,
        contract_type=contract_data.contract_type,
        provider_name=contract_data.provider_name,
        provider_contact=contract_data.provider_contact,
        start_date=contract_data.start_date,
        end_date=contract_data.end_date,
        renewal_date=renewal_date,
        amount=contract_data.amount,
        currency=contract_data.currency,
        auto_renew=contract_data.auto_renew,
        file_path=contract_data.file_path
    )
    db.add(new_contract)
    db.commit()
    db.refresh(new_contract)
    
    contract_dict = {
        "id": new_contract.id,
        "condominium_id": new_contract.condominium_id,
        "created_by": new_contract.created_by,
        "title": new_contract.title,
        "description": new_contract.description,
        "contract_type": new_contract.contract_type,
        "provider_name": new_contract.provider_name,
        "provider_contact": new_contract.provider_contact,
        "start_date": new_contract.start_date,
        "end_date": new_contract.end_date,
        "renewal_date": new_contract.renewal_date,
        "amount": new_contract.amount,
        "currency": new_contract.currency,
        "status": new_contract.status,
        "auto_renew": new_contract.auto_renew,
        "file_path": new_contract.file_path,
        "notification_sent": new_contract.notification_sent,
        "created_at": new_contract.created_at,
        "updated_at": new_contract.updated_at,
        "creator_name": current_user.full_name,
        "days_until_renewal": (new_contract.renewal_date - date.today()).days if new_contract.renewal_date else None,
    }
    return contract_dict

@router.get("/", response_model=List[ContractResponse])
def get_contracts(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view contracts"
        )
    
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    query = db.query(Contract).filter(
        Contract.condominium_id == current_user.condominium_id
    )
    
    if status_filter:
        query = query.filter(Contract.status == status_filter)
    
    contracts = query.order_by(Contract.end_date.asc()).all()
    
    result = []
    for contract in contracts:
        creator = db.query(User).filter(User.id == contract.created_by).first()
        days_until_renewal = None
        if contract.renewal_date:
            days_until_renewal = (contract.renewal_date - date.today()).days
        
        contract_dict = {
            "id": contract.id,
            "condominium_id": contract.condominium_id,
            "created_by": contract.created_by,
            "title": contract.title,
            "description": contract.description,
            "contract_type": contract.contract_type,
            "provider_name": contract.provider_name,
            "provider_contact": contract.provider_contact,
            "start_date": contract.start_date,
            "end_date": contract.end_date,
            "renewal_date": contract.renewal_date,
            "amount": contract.amount,
            "currency": contract.currency,
            "status": contract.status,
            "auto_renew": contract.auto_renew,
            "file_path": contract.file_path,
            "notification_sent": contract.notification_sent,
            "created_at": contract.created_at,
            "updated_at": contract.updated_at,
            "creator_name": creator.full_name if creator else None,
            "days_until_renewal": days_until_renewal,
        }
        result.append(contract_dict)
    
    return result

@router.get("/renewals", response_model=List[ContractResponse])
def get_upcoming_renewals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene contratos que están próximos a renovarse (dentro de 30 días)"""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view contracts"
        )
    
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    today = date.today()
    thirty_days_later = today + timedelta(days=30)
    
    contracts = db.query(Contract).filter(
        Contract.condominium_id == current_user.condominium_id,
        Contract.status == "active",
        Contract.renewal_date >= today,
        Contract.renewal_date <= thirty_days_later,
        Contract.notification_sent == False
    ).order_by(Contract.renewal_date.asc()).all()
    
    result = []
    for contract in contracts:
        creator = db.query(User).filter(User.id == contract.created_by).first()
        days_until_renewal = (contract.renewal_date - today).days
        
        # Crear aviso automático si está dentro de 1 mes
        if days_until_renewal <= 30 and not contract.notification_sent:
            announcement = Announcement(
                condominium_id=current_user.condominium_id,
                created_by=current_user.id,
                title=f"Renovación de Contrato: {contract.title}",
                content=f"El contrato con {contract.provider_name} vence el {contract.end_date.strftime('%d/%m/%Y')}. Fecha de renovación: {contract.renewal_date.strftime('%d/%m/%Y')}",
                category="contract",
                priority="high",
                target_audience="admins"
            )
            db.add(announcement)
            contract.notification_sent = True
            db.commit()
        
        contract_dict = {
            "id": contract.id,
            "condominium_id": contract.condominium_id,
            "created_by": contract.created_by,
            "title": contract.title,
            "description": contract.description,
            "contract_type": contract.contract_type,
            "provider_name": contract.provider_name,
            "provider_contact": contract.provider_contact,
            "start_date": contract.start_date,
            "end_date": contract.end_date,
            "renewal_date": contract.renewal_date,
            "amount": contract.amount,
            "currency": contract.currency,
            "status": contract.status,
            "auto_renew": contract.auto_renew,
            "file_path": contract.file_path,
            "notification_sent": contract.notification_sent,
            "created_at": contract.created_at,
            "updated_at": contract.updated_at,
            "creator_name": creator.full_name if creator else None,
            "days_until_renewal": days_until_renewal,
        }
        result.append(contract_dict)
    
    return result

@router.patch("/{contract_id}", response_model=ContractResponse)
def update_contract(
    contract_id: str,
    contract_data: ContractUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update contracts"
        )
    
    contract = db.query(Contract).filter(Contract.id == UUID(contract_id)).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    if contract.condominium_id != current_user.condominium_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = contract_data.dict(exclude_unset=True)
    
    # Recalcular renewal_date si cambió end_date
    if "end_date" in update_data:
        update_data["renewal_date"] = calculate_renewal_date(update_data["end_date"])
    
    for key, value in update_data.items():
        setattr(contract, key, value)
    
    db.commit()
    db.refresh(contract)
    
    creator = db.query(User).filter(User.id == contract.created_by).first()
    days_until_renewal = None
    if contract.renewal_date:
        days_until_renewal = (contract.renewal_date - date.today()).days
    
    contract_dict = {
        "id": contract.id,
        "condominium_id": contract.condominium_id,
        "created_by": contract.created_by,
        "title": contract.title,
        "description": contract.description,
        "contract_type": contract.contract_type,
        "provider_name": contract.provider_name,
        "provider_contact": contract.provider_contact,
        "start_date": contract.start_date,
        "end_date": contract.end_date,
        "renewal_date": contract.renewal_date,
        "amount": contract.amount,
        "currency": contract.currency,
        "status": contract.status,
        "auto_renew": contract.auto_renew,
        "file_path": contract.file_path,
        "notification_sent": contract.notification_sent,
        "created_at": contract.created_at,
        "updated_at": contract.updated_at,
        "creator_name": creator.full_name if creator else None,
        "days_until_renewal": days_until_renewal,
    }
    return contract_dict

