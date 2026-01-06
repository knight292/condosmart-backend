from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import uvicorn
from typing import List
import logging
import traceback

from app.db import engine, Base, get_db
from app.routers import auth, payments, payment_methods, tickets, visits, reservations, announcements, messages, documents, maintenances, contracts, inventory, regulations, owners, users, guard_shifts, guard_availability, shift_templates, shift_swaps, packages, reports, statistics, licenses
from app.auth import get_current_user, SECRET_KEY, ALGORITHM
from jose import jwt, JWTError
from uuid import UUID
import json

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar todos los modelos para asegurar que se registren en Base.metadata antes de crear las tablas
from app.models import (
    User, Condominium, Owner, Unit, Payment, PaymentMethod,
    Ticket, TicketAttachment, Visit, Reservation, Announcement,
    Message, Document, Maintenance, Contract, InventoryItem,
    Regulation, GuardShift, GuardAvailability, ShiftTemplate, ShiftSwap, Package, License
)

# Crear todas las tablas (incluyendo payment_methods)
Base.metadata.create_all(bind=engine)

# Función para inicializar usuarios de prueba (solo si no existen)
def initialize_test_users():
    """Inicializa usuarios de prueba si no existen - NO BORRA usuarios existentes"""
    from app.auth import get_password_hash
    from app.models.uuid_helper import USE_SQLITE
    import uuid
    
    db = next(get_db())
    try:
        # Verificar si ya existen usuarios
        existing_count = db.query(User).count()
        if existing_count > 0:
            logger.info(f"✅ Ya existen {existing_count} usuarios en la base de datos. No se crearán usuarios de prueba.")
            return
        
        logger.info("🔄 Inicializando usuarios de prueba...")
        
        # 1. Crear condominio de prueba
        condominium = db.query(Condominium).first()
        if not condominium:
            condo_id = str(uuid.uuid4()) if USE_SQLITE else uuid.uuid4()
            condominium = Condominium(
                id=condo_id,
                name="Condominio Prueba",
                address="Calle Prueba 123",
                subscription_plan="premium",
                subscription_status="active"
            )
            db.add(condominium)
            db.commit()
            db.refresh(condominium)
            logger.info("✅ Condominio de prueba creado")
        
        # 1.5. Crear y activar licencia de prueba para el condominio
        from app.models import License
        from datetime import datetime
        
        # Verificar si el condominio ya tiene licencia
        if not condominium.license_id:
            # Crear licencia de prueba
            license_id = str(uuid.uuid4()) if USE_SQLITE else uuid.uuid4()
            test_license = License(
                id=license_id,
                code="CS-TEST-0000-0000",
                package_type="premium",
                max_units=None,  # Ilimitado
                max_users=None,  # Ilimitado
                activated=True,
                activated_at=datetime.utcnow(),
                purchase_price=80000,
                buyer_name="Test",
                buyer_email="test@condosmart.com"
            )
            db.add(test_license)
            db.commit()
            db.refresh(test_license)
            
            # Asociar licencia al condominio
            if USE_SQLITE:
                condominium.license_id = str(test_license.id) if test_license.id else None
            else:
                condominium.license_id = test_license.id
            db.commit()
            logger.info("✅ Licencia de prueba creada y activada para el condominio")
        
        # 2. Crear unidad de prueba
        unit = db.query(Unit).first()
        if not unit:
            unit_id = str(uuid.uuid4()) if USE_SQLITE else uuid.uuid4()
            condo_id_value = str(condominium.id) if USE_SQLITE else condominium.id
            unit = Unit(
                id=unit_id,
                condominium_id=condo_id_value,
                number="101",
                tower="Torre A",
                floor=1,
                type="apartment"
            )
            db.add(unit)
            db.commit()
            db.refresh(unit)
            logger.info("✅ Unidad de prueba creada")
        
        # 3. Crear usuarios de prueba
        condo_id_value = str(condominium.id) if USE_SQLITE else condominium.id
        unit_id_value = str(unit.id) if USE_SQLITE else unit.id
        
        usuarios = [
            {
                "email": "admin@test.com",
                "password": "test123",
                "full_name": "Administrador Test",
                "role": "admin",
                "condominium_id": condo_id_value,
            },
            {
                "email": "admin@condosmart.com",
                "password": "admin123",
                "full_name": "Super Administrador",
                "role": "super_admin",
                "condominium_id": None,
            },
            {
                "email": "juan@test.com",
                "password": "test123",
                "full_name": "Juan Pérez",
                "role": "resident",
                "condominium_id": condo_id_value,
                "unit_id": unit_id_value,
            },
        ]
        
        created_count = 0
        for user_data in usuarios:
            existing_user = db.query(User).filter(User.email == user_data["email"]).first()
            
            if not existing_user:
                new_user = User(
                    email=user_data["email"],
                    password_hash=get_password_hash(user_data["password"]),
                    full_name=user_data["full_name"],
                    role=user_data["role"],
                    condominium_id=user_data.get("condominium_id"),
                    unit_id=user_data.get("unit_id"),
                    is_active=True
                )
                db.add(new_user)
                created_count += 1
                logger.info(f"✅ Usuario creado: {user_data['email']} ({user_data['role']})")
        
        if created_count > 0:
            db.commit()
            logger.info(f"✅ {created_count} usuarios de prueba creados exitosamente")
        else:
            logger.info("ℹ️  Todos los usuarios de prueba ya existían")
            
    except Exception as e:
        logger.error(f"❌ Error inicializando usuarios de prueba: {str(e)}")
        db.rollback()
    finally:
        db.close()

# Inicializar usuarios de prueba al iniciar (solo si la base está vacía)
try:
    initialize_test_users()
except Exception as e:
    logger.warning(f"⚠️  No se pudieron inicializar usuarios de prueba: {str(e)}")

app = FastAPI(title="CondoSmart API", version="1.0.0")

# Manejo global de excepciones
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTPException: {exc.status_code} - {exc.detail}")
    logger.error(f"Request path: {request.url.path}")
    logger.error(f"Request method: {request.method}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(f"Request path: {request.url.path}")
    logger.error(f"Request method: {request.method}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(payments.router, prefix="/api/payments", tags=["payments"])
app.include_router(payment_methods.router, prefix="/api", tags=["payment-methods"])
app.include_router(tickets.router, prefix="/api/tickets", tags=["tickets"])
app.include_router(visits.router, prefix="/api/visits", tags=["visits"])
app.include_router(reservations.router, prefix="/api/reservations", tags=["reservations"])
app.include_router(announcements.router, prefix="/api/announcements", tags=["announcements"])
app.include_router(messages.router, prefix="/api/messages", tags=["messages"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(maintenances.router, prefix="/api/maintenances", tags=["maintenances"])
app.include_router(contracts.router, prefix="/api/contracts", tags=["contracts"])
app.include_router(inventory.router, prefix="/api/inventory", tags=["inventory"])
app.include_router(regulations.router, prefix="/api/regulations", tags=["regulations"])
app.include_router(owners.router, prefix="/api/owners", tags=["owners"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(guard_shifts.router, prefix="/api/guard-shifts", tags=["guard-shifts"])
app.include_router(guard_availability.router, prefix="/api/guard-availability", tags=["guard-availability"])
app.include_router(shift_templates.router, prefix="/api/shift-templates", tags=["shift-templates"])
app.include_router(shift_swaps.router, prefix="/api/shift-swaps", tags=["shift-swaps"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(statistics.router, prefix="/api/statistics", tags=["statistics"])
app.include_router(packages.router, prefix="/api/packages", tags=["packages"])
app.include_router(licenses.router, prefix="/api/licenses", tags=["licenses"])

security = HTTPBearer()
active_connections: dict = {}  # {user_id: websocket}

async def get_user_from_token(token: str, db: Session):
    """Valida el token y retorna el usuario"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        # Usar USE_SQLITE para determinar cómo buscar el usuario
        from app.models.uuid_helper import USE_SQLITE
        if USE_SQLITE:
            # En SQLite, los IDs son strings, usar directamente
            user = db.query(User).filter(User.id == user_id).first()
        else:
            # En PostgreSQL, convertir a UUID
            user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
            user = db.query(User).filter(User.id == user_uuid).first()
        return user
    except (JWTError, ValueError, TypeError):
        return None

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(None)):
    # Aceptar la conexión primero (FastAPI requiere esto para leer query params)
    await websocket.accept()
    
    if not token:
        await websocket.close(code=1008, reason="Token required")
        return
    
    # Validar token y obtener usuario
    db = next(get_db())
    user = await get_user_from_token(token, db)
    if not user or not user.condominium_id:
        await websocket.close(code=1008, reason="Invalid token")
        return
    active_connections[str(user.id)] = websocket
    
    try:
        # Enviar mensajes históricos al conectar
        print(f"🔍 [{user.email}] Buscando mensajes para condominium_id: {user.condominium_id}")
        recent_messages = db.query(Message).filter(
            Message.condominium_id == user.condominium_id,
            Message.conversation_type == "general"
        ).order_by(Message.created_at.asc()).limit(50).all()
        
        print(f"📨 [{user.email}] Conectado. Encontrados {len(recent_messages)} mensajes históricos")
        if len(recent_messages) > 0:
            print(f"   Primer mensaje: {recent_messages[0].content[:50]}...")
            print(f"   Último mensaje: {recent_messages[-1].content[:50]}...")
        
        # Enviar mensaje especial indicando inicio de mensajes históricos
        await websocket.send_text(json.dumps({
            "type": "history_start",
            "count": len(recent_messages)
        }))
        
        # Enviar cada mensaje histórico
        sent_count = 0
        for msg in recent_messages:
            sender = db.query(User).filter(User.id == msg.sender_id).first()
            message_data = {
                "type": "message",
                "id": str(msg.id),
                "sender_id": str(msg.sender_id),
                "sender_name": sender.full_name if sender else "Usuario",
                "content": msg.content,
                "timestamp": msg.created_at.isoformat(),
                "conversation_type": msg.conversation_type,
            }
            try:
                await websocket.send_text(json.dumps(message_data))
                sent_count += 1
                print(f"   ✅ [{sent_count}/{len(recent_messages)}] Enviado: {msg.content[:30]}...")
            except Exception as e:
                print(f"❌ Error enviando mensaje histórico {msg.id}: {e}")
        
        print(f"📤 [{user.email}] Total enviados: {sent_count}/{len(recent_messages)}")
        
        # Enviar mensaje especial indicando fin de mensajes históricos
        await websocket.send_text(json.dumps({
            "type": "history_end"
        }))
        
        print(f"✅ [{user.email}] Mensajes históricos enviados correctamente")
        
        # Bucle principal para recibir mensajes nuevos
        while True:
            data = await websocket.receive_text()
            message_json = json.loads(data)
            content = message_json.get("content", "").strip()
            
            if not content:
                continue
            
            # Guardar mensaje en la base de datos
            # Convertir UUIDs a string si es necesario (para SQLite)
            from app.models.uuid_helper import USE_SQLITE
            condominium_id = str(user.condominium_id) if USE_SQLITE else user.condominium_id
            sender_id = str(user.id) if USE_SQLITE else user.id
            
            new_message = Message(
                condominium_id=condominium_id,
                sender_id=sender_id,
                conversation_type=message_json.get("conversation_type", "general"),
                content=content
            )
            db.add(new_message)
            db.commit()
            db.refresh(new_message)
            
            print(f"💬 [{user.email}] Mensaje guardado: {content[:50]}...")
            
            # Preparar mensaje para enviar
            message_data = {
                "type": "message",
                "id": str(new_message.id),
                "sender_id": str(new_message.sender_id),
                "sender_name": user.full_name,
                "content": new_message.content,
                "timestamp": new_message.created_at.isoformat(),
                "conversation_type": new_message.conversation_type,
            }
            
            # Enviar a todos los usuarios del mismo condominio conectados (incluyendo el remitente)
            sent_count = 0
            disconnected_users = []
            print(f"🔍 [{user.email}] Buscando usuarios en condominio {user.condominium_id}")
            print(f"🔍 [{user.email}] Conexiones activas: {list(active_connections.keys())}")
            
            for user_id, connection in list(active_connections.items()):
                try:
                    other_user = db.query(User).filter(User.id == UUID(user_id)).first()
                    if other_user:
                        print(f"🔍 [{user.email}] Verificando usuario {other_user.email}: condominium_id={other_user.condominium_id}")
                        if other_user.condominium_id == user.condominium_id:
                            print(f"✅ [{user.email}] Enviando mensaje a {other_user.email}")
                            await connection.send_text(json.dumps(message_data))
                            sent_count += 1
                        else:
                            print(f"⚠️ [{user.email}] Usuario {other_user.email} está en otro condominio")
                    else:
                        print(f"⚠️ [{user.email}] Usuario {user_id} no encontrado en BD")
                except Exception as e:
                    print(f"❌ Error enviando a {user_id}: {e}")
                    import traceback
                    traceback.print_exc()
                    disconnected_users.append(user_id)
            
            # Limpiar conexiones desconectadas
            for user_id in disconnected_users:
                if user_id in active_connections:
                    del active_connections[user_id]
            
            print(f"📤 [{user.email}] Mensaje enviado a {sent_count} usuarios conectados del condominio {user.condominium_id}")
                    
    except WebSocketDisconnect:
        if str(user.id) in active_connections:
            del active_connections[str(user.id)]
    except Exception as e:
        print(f"WebSocket error: {e}")
        if str(user.id) in active_connections:
            del active_connections[str(user.id)]
    finally:
        db.close()

@app.get("/")
async def root():
    return {"message": "CondoSmart API"}

@app.post("/api/recreate-users")
def recreate_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Endpoint temporal para recrear usuarios de prueba - SOLO SUPER_ADMIN"""
    from fastapi import HTTPException, status
    
    # Proteger el endpoint - solo super_admin puede usarlo
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super_admin can recreate users"
        )
    from app.auth import get_password_hash
    from app.models import Condominium, Unit
    from app.models.uuid_helper import USE_SQLITE
    import uuid
    
    try:
        print("🔄 Recreando usuarios de prueba...")
        
        # 1. Crear o obtener condominio
        condominium = db.query(Condominium).first()
        if not condominium:
            # Crear ID como string si es SQLite
            condo_id = str(uuid.uuid4()) if USE_SQLITE else uuid.uuid4()
            condominium = Condominium(
                id=condo_id,
                name="Condominio Prueba",
                address="Calle Prueba 123",
                subscription_plan="small",
                subscription_status="active"
            )
            db.add(condominium)
            db.commit()
            db.refresh(condominium)
        
        # 2. Crear o obtener unidad
        unit = db.query(Unit).first()
        if not unit:
            # Crear ID como string si es SQLite
            unit_id = str(uuid.uuid4()) if USE_SQLITE else uuid.uuid4()
            # Asegurar que condominium_id sea string si es SQLite
            condo_id_value = str(condominium.id) if USE_SQLITE else condominium.id
            unit = Unit(
                id=unit_id,
                condominium_id=condo_id_value,
                number="101",
                tower="Torre A",
                floor=1,
                type="apartment"
            )
            db.add(unit)
            db.commit()
            db.refresh(unit)
        
        # 3. Crear usuarios
        # Convertir IDs a string si es SQLite
        condo_id_value = str(condominium.id) if USE_SQLITE else condominium.id
        unit_id_value = str(unit.id) if USE_SQLITE else unit.id
        
        usuarios = [
            {
                "email": "admin@test.com",
                "password": "test123",
                "full_name": "Administrador Test",
                "role": "admin",
                "condominium_id": condo_id_value,
            },
            {
                "email": "admin@condosmart.com",
                "password": "admin123",
                "full_name": "Super Administrador",
                "role": "super_admin",
                "condominium_id": None,
            },
            {
                "email": "juan@test.com",
                "password": "test123",
                "full_name": "Juan Pérez",
                "role": "resident",
                "condominium_id": condo_id_value,
                "unit_id": unit_id_value,
            },
        ]
        
        created_users = []
        for user_data in usuarios:
            existing_user = db.query(User).filter(User.email == user_data["email"]).first()
            
            if existing_user:
                existing_user.password_hash = get_password_hash(user_data["password"])
                existing_user.full_name = user_data["full_name"]
                existing_user.role = user_data["role"]
                existing_user.condominium_id = user_data.get("condominium_id")
                existing_user.unit_id = user_data.get("unit_id")
                existing_user.is_active = True
                db.commit()
                created_users.append({"email": user_data["email"], "status": "updated"})
            else:
                new_user = User(
                    email=user_data["email"],
                    password_hash=get_password_hash(user_data["password"]),
                    full_name=user_data["full_name"],
                    role=user_data["role"],
                    condominium_id=user_data.get("condominium_id"),
                    unit_id=user_data.get("unit_id"),
                    is_active=True
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                created_users.append({"email": user_data["email"], "status": "created", "id": str(new_user.id)})
        
        return {
            "message": "Usuarios recreados exitosamente",
            "users": created_users
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error recreando usuarios: {str(e)}"
        )

@app.post("/api/init-production")
async def init_production_data(db: Session = Depends(get_db)):
    """
    Endpoint para inicializar datos de producción.
    Solo se puede ejecutar una vez (verifica si ya existen usuarios).
    """
    from app.models import User, Condominium, Owner
    from app.auth import get_password_hash
    import uuid
    
    try:
        # Verificar si ya existe un super admin
        existing_super_admin = db.query(User).filter(User.role == "super_admin").first()
        if existing_super_admin:
            return {
                "message": "Los datos ya están inicializados",
                "users_exist": True,
                "super_admin": existing_super_admin.email
            }
        
        # Obtener el tipo UUID correcto según la base de datos
        from app.models.uuid_helper import UUID
        import os
        DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test_condosmart.db")
        USE_SQLITE = "sqlite" in DATABASE_URL
        
        # Crear IDs
        if USE_SQLITE:
            super_admin_id = str(uuid.uuid4())
            admin_id = str(uuid.uuid4())
            owner_id = str(uuid.uuid4())
            condominium_id = str(uuid.uuid4())
            resident_id = str(uuid.uuid4())
        else:
            super_admin_id = uuid.uuid4()
            admin_id = uuid.uuid4()
            owner_id = uuid.uuid4()
            condominium_id = uuid.uuid4()
            resident_id = uuid.uuid4()
        
        # Crear Super Admin (verificar si ya existe y actualizar rol)
        existing_super = db.query(User).filter(User.email == "admin@condosmart.com").first()
        if existing_super:
            existing_super.role = "super_admin"
            existing_super.password_hash = get_password_hash("admin123")
            db.commit()
            print("✅ Super Admin actualizado")
        else:
            super_admin = User(
                id=super_admin_id,
                email="admin@condosmart.com",
                password_hash=get_password_hash("admin123"),
                full_name="Super Administrador",
                role="super_admin",
                is_active=True
            )
            db.add(super_admin)
            db.flush()
        db.add(super_admin)
        db.flush()
        
        # Crear Owner y Condominio de prueba
        owner = Owner(
            id=owner_id,
            name="Empresa de Prueba",
            email="owner@test.com",
            phone="1234567890",
            is_active="active"
        )
        db.add(owner)
        db.flush()
        
        condominium = Condominium(
            id=condominium_id,
            owner_id=owner.id,
            name="Condominio de Prueba",
            address="Dirección de Prueba",
            subscription_plan="premium",
            subscription_status="active"
        )
        db.add(condominium)
        db.flush()
        
        # Crear Admin de prueba
        admin = User(
            id=admin_id,
            email="admin@test.com",
            password_hash=get_password_hash("test123"),
            full_name="Administrador de Prueba",
            role="admin",
            condominium_id=condominium.id,
            is_active=True
        )
        db.add(admin)
        db.flush()
        
        # Crear Residente de prueba
        resident = User(
            id=resident_id,
            email="juan@test.com",
            password_hash=get_password_hash("test123"),
            full_name="Juan Pérez",
            role="resident",
            condominium_id=condominium.id,
            is_active=True
        )
        db.add(resident)
        db.commit()
        
        return {
            "message": "Datos de producción inicializados correctamente",
            "users_created": {
                "super_admin": {
                    "email": "admin@condosmart.com",
                    "password": "admin123"
                },
                "admin": {
                    "email": "admin@test.com",
                    "password": "test123"
                },
                "resident": {
                    "email": "juan@test.com",
                    "password": "test123"
                }
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error inicializando datos: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

