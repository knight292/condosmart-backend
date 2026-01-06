from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db import get_db
from app.models import Message, User
from app.schemas.message import MessageCreate, MessageResponse
from app.auth import get_current_user

router = APIRouter()

@router.get("/", response_model=List[MessageResponse])
def get_messages(
    conversation_type: Optional[str] = Query("general", description="Tipo de conversación: general, private"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    query = db.query(Message).filter(
        Message.condominium_id == current_user.condominium_id,
        Message.conversation_type == conversation_type
    )
    
    # Si es conversación privada, filtrar por sender o receiver
    if conversation_type == "private":
        query = query.filter(
            (Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)
        )
    
    messages = query.order_by(Message.created_at.asc()).all()
    
    # Agregar información del sender
    result = []
    for message in messages:
        sender = db.query(User).filter(User.id == message.sender_id).first()
        message_dict = {
            "id": message.id,
            "condominium_id": message.condominium_id,
            "sender_id": message.sender_id,
            "receiver_id": message.receiver_id,
            "conversation_type": message.conversation_type,
            "tower": message.tower,
            "content": message.content,
            "is_read": message.is_read,
            "created_at": message.created_at,
            "sender_name": sender.full_name if sender else "Usuario",
        }
        result.append(message_dict)
    
    return result

@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    # Convertir UUIDs a string si es necesario (para SQLite)
    from app.models.uuid_helper import USE_SQLITE
    condominium_id = str(current_user.condominium_id) if USE_SQLITE else current_user.condominium_id
    sender_id = str(current_user.id) if USE_SQLITE else current_user.id
    receiver_id = str(message_data.receiver_id) if (USE_SQLITE and message_data.receiver_id) else message_data.receiver_id
    
    new_message = Message(
        condominium_id=condominium_id,
        sender_id=sender_id,
        receiver_id=receiver_id,
        conversation_type=message_data.conversation_type,
        tower=message_data.tower,
        content=message_data.content
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    
    # Agregar información del sender
    message_dict = {
        "id": new_message.id,
        "condominium_id": new_message.condominium_id,
        "sender_id": new_message.sender_id,
        "receiver_id": new_message.receiver_id,
        "conversation_type": new_message.conversation_type,
        "tower": new_message.tower,
        "content": new_message.content,
        "is_read": new_message.is_read,
        "created_at": new_message.created_at,
        "sender_name": current_user.full_name,
    }
    return message_dict

