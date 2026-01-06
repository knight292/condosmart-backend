#!/usr/bin/env python3
"""
Script para recrear usuarios de prueba después de cambios en UUID
"""
from app.db import SessionLocal, engine, Base
from app.models import User, Condominium, Unit
from app.auth import get_password_hash
from app.models.uuid_helper import USE_SQLITE
import uuid

# Crear todas las tablas
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    print("🔄 Recreando usuarios de prueba...")
    print(f"📊 Usando SQLite: {USE_SQLITE}")
    print("")
    
    # 1. Crear o obtener condominio
    condominium = db.query(Condominium).first()
    if not condominium:
        from app.models.condominium import Condominium
        condominium = Condominium(
            name="Condominio Prueba",
            address="Calle Prueba 123",
            subscription_plan="small",
            subscription_status="active"
        )
        db.add(condominium)
        db.commit()
        db.refresh(condominium)
        print(f"✅ Condominio creado: {condominium.id}")
    else:
        print(f"✅ Condominio existente: {condominium.id}")
    
    # 2. Crear o obtener unidad
    unit = db.query(Unit).first()
    if not unit:
        from app.models.unit import Unit
        unit = Unit(
            condominium_id=condominium.id,
            number="101",
            tower="Torre A",
            floor=1,
            type="apartment"
        )
        db.add(unit)
        db.commit()
        db.refresh(unit)
        print(f"✅ Unidad creada: {unit.id}")
    else:
        print(f"✅ Unidad existente: {unit.id}")
    
    # 3. Crear usuarios
    usuarios = [
        {
            "email": "admin@test.com",
            "password": "test123",
            "full_name": "Administrador Test",
            "role": "admin",
            "condominium_id": condominium.id,
        },
        {
            "email": "admin@condosmart.com",
            "password": "admin123",
            "full_name": "Super Administrador",
            "role": "super_admin",
            "condominium_id": None,  # Super admin no tiene condominio
        },
        {
            "email": "juan@test.com",
            "password": "test123",
            "full_name": "Juan Pérez",
            "role": "resident",
            "condominium_id": condominium.id,
            "unit_id": unit.id,
        },
    ]
    
    for user_data in usuarios:
        # Verificar si el usuario ya existe
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        
        if existing_user:
            # Actualizar usuario existente
            existing_user.password_hash = get_password_hash(user_data["password"])
            existing_user.full_name = user_data["full_name"]
            existing_user.role = user_data["role"]
            existing_user.condominium_id = user_data.get("condominium_id")
            existing_user.unit_id = user_data.get("unit_id")
            existing_user.is_active = True
            db.commit()
            print(f"✅ Usuario actualizado: {user_data['email']} / {user_data['password']}")
        else:
            # Crear nuevo usuario
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
            print(f"✅ Usuario creado: {user_data['email']} / {user_data['password']} (ID: {new_user.id}, Tipo: {type(new_user.id)})")
    
    print("")
    print("=" * 60)
    print("✅ USUARIOS RECREADOS EXITOSAMENTE")
    print("=" * 60)
    print("")
    print("👤 CREDENCIALES:")
    print("")
    print("   ADMIN:")
    print("   Email: admin@test.com")
    print("   Password: test123")
    print("")
    print("   SUPER ADMIN:")
    print("   Email: admin@condosmart.com")
    print("   Password: admin123")
    print("")
    print("   RESIDENTE:")
    print("   Email: juan@test.com")
    print("   Password: test123")
    print("")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()
