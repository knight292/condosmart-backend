from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.db import get_db
from app.models import Ticket, TicketAttachment, User
from app.models.uuid_helper import USE_SQLITE
from app.schemas.ticket import TicketCreate, TicketResponse, TicketUpdate
from app.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    ticket_data: TicketCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    # Convertir IDs a string si es SQLite
    condo_id = str(current_user.condominium_id) if USE_SQLITE else current_user.condominium_id
    user_id = str(current_user.id) if USE_SQLITE else current_user.id
    
    new_ticket = Ticket(
        condominium_id=condo_id,
        reported_by=user_id,
        category=ticket_data.category,
        title=ticket_data.title,
        description=ticket_data.description,
        priority=ticket_data.priority,
        status="new"
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    return new_ticket

@router.post("/{ticket_id}/attachments", status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    ticket_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id,
        Ticket.reported_by == current_user.id
    ).first()
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    file_url = f"uploads/{ticket_id}/{uuid.uuid4()}_{file.filename}"
    
    attachment = TicketAttachment(
        ticket_id=ticket.id,
        file_url=file_url,
        file_type=file.content_type
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    
    return {"id": str(attachment.id), "file_url": file_url}

@router.get("/", response_model=List[TicketResponse])
def get_tickets(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Ticket)
    
    if current_user.role == "resident":
        query = query.filter(Ticket.reported_by == current_user.id)
    elif current_user.role in ["admin", "super_admin"]:
        if current_user.condominium_id:
            query = query.filter(Ticket.condominium_id == current_user.condominium_id)
    elif current_user.role == "owner":
        # Owners pueden ver tickets del condominio seleccionado (asignado temporalmente en auth.py)
        if current_user.condominium_id:
            query = query.filter(Ticket.condominium_id == current_user.condominium_id)
    
    if status_filter:
        query = query.filter(Ticket.status == status_filter)
    
    tickets = query.order_by(Ticket.created_at.desc()).all()
    return tickets

@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    if current_user.role == "resident" and ticket.reported_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    return ticket

@router.patch("/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    ticket_id: str,
    ticket_update: TicketUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from datetime import datetime
    from uuid import UUID
    
    # Convertir el string a UUID si es necesario
    try:
        ticket_uuid = UUID(ticket_id) if isinstance(ticket_id, str) else ticket_id
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ticket ID format"
        )
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_uuid).first()
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update tickets"
        )
    
    if ticket_update.status:
        ticket.status = ticket_update.status
        # Si se marca como resuelto, actualizar resolved_at
        if ticket_update.status == "resolved":
            ticket.resolved_at = datetime.utcnow()
    if ticket_update.assigned_to:
        ticket.assigned_to = ticket_update.assigned_to
    if ticket_update.priority:
        ticket.priority = ticket_update.priority
    
    db.commit()
    db.refresh(ticket)
    return ticket

