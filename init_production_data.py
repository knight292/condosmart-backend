#!/usr/bin/env python3
"""
Script para inicializar datos en producción
Ejecutar en Railway: railway run python init_production_data.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.db import SessionLocal, engine, Base
from app.models import User, Condominium, Owner
from app.auth import get_password_hash
import uuid

# Crear todas las tablas
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    print("🔧 Inicializando datos de producción...")
    
    # Verificar si ya existe un super admin
    existing_super_admin = db.query(User).filter(User.role == "super_admin").first()
    if existing_super_admin:
        print("⚠️  Ya existe un super admin. Saltando creación...")
    else:
        # Crear Super Admin
        print("📝 Creando Super Admin...")
        super_admin = User(
            id=uuid.uuid4(),
            email="admin@condosmart.com",
            password_hash=get_password_hash("admin123"),
            full_name="Super Administrador",
            role="super_admin",
            is_active=True
        )
        db.add(super_admin)
        db.commit()
        print("✅ Super Admin creado:")
        print(f"   Email: admin@condosmart.com")
        print(f"   Password: admin123")
    
    # Verificar si ya existe un admin de prueba
    existing_admin = db.query(User).filter(User.email == "admin@test.com").first()
    if existing_admin:
        print("⚠️  Ya existe admin@test.com. Saltando creación...")
    else:
        # Crear Admin de prueba
        print("📝 Creando Admin de prueba...")
        admin = User(
            id=uuid.uuid4(),
            email="admin@test.com",
            password_hash=get_password_hash("test123"),
            full_name="Administrador de Prueba",
            role="admin",
            is_active=True
        )
        db.add(admin)
        db.commit()
        print("✅ Admin creado:")
        print(f"   Email: admin@test.com")
        print(f"   Password: test123")
    
    # Verificar si ya existe un residente de prueba
    existing_resident = db.query(User).filter(User.email == "juan@test.com").first()
    if existing_resident:
        print("⚠️  Ya existe juan@test.com. Saltando creación...")
    else:
        # Crear Owner y Condominio de prueba
        print("📝 Creando Owner y Condominio de prueba...")
        owner = Owner(
            id=uuid.uuid4(),
            name="Empresa de Prueba",
            email="owner@test.com",
            phone="1234567890",
            is_active="active"
        )
        db.add(owner)
        db.flush()
        
        condominium = Condominium(
            id=uuid.uuid4(),
            owner_id=owner.id,
            name="Condominio de Prueba",
            address="Dirección de Prueba",
            subscription_plan="premium",
            subscription_status="active"
        )
        db.add(condominium)
        db.flush()
        
        # Crear Residente de prueba
        resident = User(
            id=uuid.uuid4(),
            email="juan@test.com",
            password_hash=get_password_hash("test123"),
            full_name="Juan Pérez",
            role="resident",
            condominium_id=condominium.id,
            is_active=True
        )
        db.add(resident)
        db.commit()
        print("✅ Residente creado:")
        print(f"   Email: juan@test.com")
        print(f"   Password: test123")
        print(f"   Condominio: {condominium.name}")
    
    print("")
    print("✅ Inicialización completada!")
    print("")
    print("📋 USUARIOS CREADOS:")
    print("   1. Super Admin: admin@condosmart.com / admin123")
    print("   2. Admin: admin@test.com / test123")
    print("   3. Residente: juan@test.com / test123")
    print("")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()
