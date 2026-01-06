from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
from uuid import UUID
import logging

from app.db import get_db
from app.models import Payment, User, PaymentMethod
from app.models.uuid_helper import USE_SQLITE
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentProcess
from app.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    payment_data: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crear un pago.
    - Si es admin/super_admin: puede crear pagos para cualquier residente de su condominio (debe especificar user_id)
    - Si es resident: solo puede crear pagos para sí mismo
    """
    # Determinar para qué usuario se crea el pago
    target_user_id = None
    target_user = None
    
    if current_user.role in ["admin", "super_admin", "owner"]:
        # Administradores pueden crear pagos para residentes específicos
        if payment_data.user_id:
            # Si se especifica un user_id, crear para ese usuario
            if USE_SQLITE:
                target_user_id = str(payment_data.user_id) if payment_data.user_id else None
            else:
                target_user_id = payment_data.user_id
            
            # Verificar que el usuario existe
            target_user = db.query(User).filter(User.id == target_user_id).first() if target_user_id else None
            if not target_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuario no encontrado"
                )
            
            # Verificar que pertenece al mismo condominio
            if USE_SQLITE:
                target_condo_id = str(target_user.condominium_id) if target_user.condominium_id else None
                user_condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
            else:
                target_condo_id = target_user.condominium_id
                user_condo_id = current_user.condominium_id
            
            if target_condo_id != user_condo_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo puedes crear pagos para usuarios de tu condominio"
                )
            
            # Verificar que el usuario objetivo es residente o guardia
            if target_user.role not in ["resident", "guard"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Solo puedes crear pagos para residentes o guardias"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debes especificar el user_id del residente para crear el pago"
            )
    elif current_user.role == "resident":
        # Residentes solo pueden crear pagos para sí mismos
        target_user_id = str(current_user.id) if (USE_SQLITE and current_user.id) else current_user.id
        target_user = current_user
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para crear pagos"
        )
    
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    # Convertir IDs a string si es SQLite
    condo_id = str(current_user.condominium_id) if (USE_SQLITE and current_user.condominium_id) else current_user.condominium_id
    
    new_payment = Payment(
        user_id=target_user_id,
        condominium_id=condo_id,
        amount=payment_data.amount,
        currency=payment_data.currency,
        payment_method=payment_data.payment_method,
        due_date=payment_data.due_date,
        status="pending"
    )
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)
    
    # Agregar información del usuario
    payment_dict = {
        "id": new_payment.id,
        "user_id": new_payment.user_id,
        "condominium_id": new_payment.condominium_id,
        "amount": new_payment.amount,
        "currency": new_payment.currency,
        "status": new_payment.status,
        "payment_method": new_payment.payment_method,
        "payment_gateway": new_payment.payment_gateway,
        "gateway_transaction_id": new_payment.gateway_transaction_id,
        "due_date": new_payment.due_date,
        "paid_at": new_payment.paid_at,
        "created_at": new_payment.created_at,
        "user_name": target_user.full_name if target_user else None,
        "user_email": target_user.email if target_user else None,
    }
    
    # Agregar notificación para el usuario
    try:
        from app.services.notification_service import NotificationService
        notification_service = NotificationService()
        notification_service.add_notification(
            user_id=str(target_user.id) if (USE_SQLITE and target_user.id) else target_user.id,
            title="Nuevo pago pendiente",
            message=f"Tienes un pago pendiente de ${payment_data.amount} {payment_data.currency} con vencimiento el {payment_data.due_date.strftime('%d/%m/%Y')}",
            type="payment"
        )
    except Exception as e:
        logger.warning(f"No se pudo crear notificación: {str(e)}")
    
    return payment_dict

@router.get("", response_model=List[PaymentResponse])
@router.get("/", response_model=List[PaymentResponse])
def get_payments(
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from sqlalchemy.orm import joinedload
    
    query = db.query(Payment)
    
    # Convertir IDs a string si es SQLite
    if USE_SQLITE:
        user_id = str(current_user.id) if current_user.id else None
        condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
    else:
        user_id = current_user.id
        condo_id = current_user.condominium_id
    
    # Si es residente, solo sus pagos. Si es admin u owner, todos los del condominio
    # Los guardias NO pueden ver pagos
    if current_user.role == "guard":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Los guardias no tienen acceso a los pagos"
        )
    elif current_user.role == "resident":
        if user_id:
            query = query.filter(Payment.user_id == user_id)
    elif current_user.role in ["admin", "super_admin", "owner"]:
        if condo_id:
            query = query.filter(Payment.condominium_id == condo_id)
    
    if status_filter:
        query = query.filter(Payment.status == status_filter)
    
    payments = query.order_by(Payment.created_at.desc()).all()
    
    # Agregar información del usuario a cada pago
    result = []
    for payment in payments:
        # Convertir ID para la query si es SQLite
        if USE_SQLITE:
            payment_user_id = str(payment.user_id) if payment.user_id else None
        else:
            payment_user_id = payment.user_id
        
        user = db.query(User).filter(User.id == payment_user_id).first() if payment_user_id else None
        payment_dict = {
            "id": payment.id,
            "user_id": payment.user_id,
            "condominium_id": payment.condominium_id,
            "amount": payment.amount,
            "currency": payment.currency,
            "status": payment.status,
            "payment_method": payment.payment_method,
            "payment_gateway": payment.payment_gateway,
            "gateway_transaction_id": payment.gateway_transaction_id,
            "due_date": payment.due_date,
            "paid_at": payment.paid_at,
            "created_at": payment.created_at,
            "user_name": user.full_name if user else None,
            "user_email": user.email if user else None,
        }
        result.append(payment_dict)
    
    return result

@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Convertir ID a string si es SQLite
    user_id = str(current_user.id) if (USE_SQLITE and current_user.id) else current_user.id
    
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.user_id == user_id
    ).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    return payment

@router.post("/{payment_id}/process", response_model=PaymentResponse)
def process_payment(
    payment_id: str,
    process_data: PaymentProcess,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Procesar un pago con un método de pago específico"""
    from uuid import UUID as UUIDType
    
    # Verificar que el pago existe y pertenece al usuario
    try:
        payment_uuid = UUIDType(payment_id) if isinstance(payment_id, str) else payment_id
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment ID format"
        )
    
    # Convertir ID a string si es SQLite
    user_id = str(current_user.id) if (USE_SQLITE and current_user.id) else current_user.id
    
    payment = db.query(Payment).filter(
        Payment.id == payment_uuid,
        Payment.user_id == user_id
    ).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    if payment.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment is already {payment.status}"
        )
    
    # Verificar que el método de pago existe y está activo
    try:
        method_uuid = UUIDType(process_data.payment_method_id) if isinstance(process_data.payment_method_id, str) else process_data.payment_method_id
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment method ID format"
        )
    
    # Convertir condominium_id a string si es SQLite
    condo_id = str(current_user.condominium_id) if (USE_SQLITE and current_user.condominium_id) else current_user.condominium_id
    
    payment_method = db.query(PaymentMethod).filter(
        PaymentMethod.id == method_uuid,
        PaymentMethod.condominium_id == condo_id,
        PaymentMethod.is_active == True
    ).first()
    
    if not payment_method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment method not found or inactive"
        )
    
    # Procesar según el tipo de método
    if payment_method.method_type == "bank_deposit":
        # Depósito bancario: marcar como pendiente de verificación
        payment.status = "pending_verification"
        payment.payment_method = payment_method.name
        payment.payment_gateway = None
        # No marcamos paid_at todavía, espera verificación del admin
        
    elif payment_method.method_type == "spei":
        # Transferencia SPEI: también requiere verificación manual
        # (a menos que se integre con una pasarela que confirme automáticamente)
        if payment_method.gateway_name:
            # Si tiene gateway configurado, se procesa automáticamente
            payment.status = "completed"
            payment.payment_gateway = payment_method.gateway_name
            payment.gateway_transaction_id = f"SPEI-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            payment.paid_at = datetime.utcnow()
        else:
            # Sin gateway: requiere verificación manual
            payment.status = "pending_verification"
            payment.payment_gateway = None
        payment.payment_method = payment_method.name
        
    elif payment_method.method_type in ["card", "oxxo"]:
        # Pasarelas de pago: aquí se integraría con el gateway real (Stripe, MercadoPago, etc.)
        # Por ahora, simulamos que se procesa exitosamente
        payment.status = "completed"
        payment.payment_method = payment_method.name
        payment.payment_gateway = payment_method.gateway_name or "simulated"
        payment.gateway_transaction_id = f"TXN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        payment.paid_at = datetime.utcnow()
        
    else:
        # Otros métodos: marcar como completado
        payment.status = "completed"
        payment.payment_method = payment_method.name
        payment.paid_at = datetime.utcnow()
    
    db.commit()
    db.refresh(payment)
    
    # Obtener información del usuario para la respuesta
    # Convertir ID para la query si es SQLite
    if USE_SQLITE:
        payment_user_id = str(payment.user_id) if payment.user_id else None
    else:
        payment_user_id = payment.user_id
    
    user = db.query(User).filter(User.id == payment_user_id).first() if payment_user_id else None
    payment_dict = {
        "id": payment.id,
        "user_id": payment.user_id,
        "condominium_id": payment.condominium_id,
        "amount": payment.amount,
        "currency": payment.currency,
        "status": payment.status,
        "payment_method": payment.payment_method,
        "payment_gateway": payment.payment_gateway,
        "gateway_transaction_id": payment.gateway_transaction_id,
        "due_date": payment.due_date,
        "paid_at": payment.paid_at,
        "created_at": payment.created_at,
        "user_name": user.full_name if user else None,
        "user_email": user.email if user else None,
    }
    
    return payment_dict
