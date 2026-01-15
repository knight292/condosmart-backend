from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.db import get_db
from app.models import Ticket, TicketAttachment, User, Notification
from app.models.uuid_helper import USE_SQLITE
from app.schemas.ticket import TicketCreate, TicketResponse, TicketUpdate
from app.auth import get_current_user
from app.services.fcm_service import FCMService

router = APIRouter()

@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
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
    
    # Crear notificaciones para admins y reporte del residente
    try:
        notifications = []
        fcm_service = FCMService()
        # Notificar al residente que creó el ticket
        notifications.append(Notification(
            user_id=user_id,
            condominium_id=condo_id,
            title="Ticket creado",
            message=f"Tu ticket '{new_ticket.title}' fue creado exitosamente.",
            type="ticket",
            action_id=str(new_ticket.id),
            data={"ticket_id": str(new_ticket.id)}
        ))
        if current_user.fcm_token:
            fcm_service.send_notification(
                device_token=current_user.fcm_token,
                title="Ticket creado",
                body=f"Tu ticket '{new_ticket.title}' fue creado exitosamente.",
                data={"type": "ticket", "ticket_id": str(new_ticket.id)}
            )
        
        admins = db.query(User).filter(
            User.condominium_id == condo_id,
            User.role.in_(["admin", "owner"])
        ).all()
        for admin in admins:
            admin_id = str(admin.id) if USE_SQLITE else admin.id
            notifications.append(Notification(
                user_id=admin_id,
                condominium_id=condo_id,
                title="Nuevo ticket reportado",
                message=f"{current_user.full_name} reportó: {new_ticket.title}",
                type="ticket",
                action_id=str(new_ticket.id),
                data={"ticket_id": str(new_ticket.id), "reported_by": str(current_user.id)}
            ))
            if admin.fcm_token:
                fcm_service.send_notification(
                    device_token=admin.fcm_token,
                    title="Nuevo ticket reportado",
                    body=f"{current_user.full_name} reportó: {new_ticket.title}",
                    data={"type": "ticket", "ticket_id": str(new_ticket.id)}
                )
        if notifications:
            db.add_all(notifications)
            db.commit()
    except Exception as e:
        print(f"⚠️ No se pudieron crear notificaciones de ticket: {e}")
    return new_ticket

@router.post("/{ticket_id}/attachments", status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    ticket_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Convertir IDs a string si es SQLite
    user_id = str(current_user.id) if USE_SQLITE else current_user.id
    
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id,
        Ticket.reported_by == user_id
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

@router.get("", response_model=List[TicketResponse])
@router.get("/", response_model=List[TicketResponse])
def get_tickets(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    import logging
    logger = logging.getLogger(__name__)
    logger.info("get_tickets called")
    
    try:
        query = db.query(Ticket)
        
        # Convertir IDs a string si es SQLite para las comparaciones
        if USE_SQLITE:
            user_id = str(current_user.id) if current_user.id else None
            condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
        else:
            user_id = current_user.id
            condo_id = current_user.condominium_id
        
        logger.info(f"User role: {current_user.role}, user_id: {user_id}, condo_id: {condo_id}")
        
        # Los guardias NO pueden ver tickets
        if current_user.role == "guard":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Los guardias no tienen acceso a los tickets"
            )
        elif current_user.role == "resident":
            if user_id:
                query = query.filter(Ticket.reported_by == user_id)
            else:
                # Si no tiene user_id, devolver lista vacía
                return []
        elif current_user.role == "admin":
            if condo_id:
                query = query.filter(Ticket.condominium_id == condo_id)
            else:
                # Si no tiene condo_id, devolver lista vacía
                return []
        elif current_user.role == "owner":
            # Owners pueden ver tickets del condominio seleccionado (asignado temporalmente en auth.py)
            if condo_id:
                query = query.filter(Ticket.condominium_id == condo_id)
            else:
                # Si no tiene condo_id, devolver lista vacía
                return []
        else:
            # Rol no reconocido, devolver lista vacía
            return []
        
        if status_filter:
            query = query.filter(Ticket.status == status_filter)
        
        tickets = query.order_by(Ticket.created_at.desc()).all()
        logger.info(f"Found {len(tickets)} tickets")
        return tickets
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying tickets: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving tickets: {str(e)}"
        )

@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # En SQLite, los IDs son strings, usar directamente
    # En PostgreSQL, convertir a UUID si es necesario
    if USE_SQLITE:
        ticket_search_id = ticket_id
    else:
        from uuid import UUID
        try:
            ticket_search_id = UUID(ticket_id) if isinstance(ticket_id, str) else ticket_id
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ticket ID format"
            )
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_search_id).first()
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    # Convertir IDs a string si es SQLite para la comparación
    if USE_SQLITE:
        user_id = str(current_user.id) if current_user.id else None
        ticket_reported_by = str(ticket.reported_by) if ticket.reported_by else None
    else:
        user_id = current_user.id
        ticket_reported_by = ticket.reported_by
    
    if current_user.role == "resident" and ticket_reported_by != user_id:
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
    import logging
    logger = logging.getLogger(__name__)
    
    # En SQLite, los IDs son strings, usar directamente
    # En PostgreSQL, convertir a UUID
    if USE_SQLITE:
        ticket_search_id = ticket_id
    else:
        from uuid import UUID
        try:
            ticket_search_id = UUID(ticket_id) if isinstance(ticket_id, str) else ticket_id
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ticket ID format"
            )
    
    logger.info(f"Searching for ticket with ID: {ticket_search_id}, type: {type(ticket_search_id)}, USE_SQLITE: {USE_SQLITE}")
    ticket = db.query(Ticket).filter(Ticket.id == ticket_search_id).first()
    
    if not ticket:
        logger.error(f"Ticket not found with ID: {ticket_search_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    if current_user.role != "admin":
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
        # Convertir assigned_to a string si es SQLite
        if USE_SQLITE:
            ticket.assigned_to = str(ticket_update.assigned_to) if ticket_update.assigned_to else None
        else:
            ticket.assigned_to = ticket_update.assigned_to
    if ticket_update.priority:
        ticket.priority = ticket_update.priority
    
    db.commit()
    db.refresh(ticket)
    return ticket

