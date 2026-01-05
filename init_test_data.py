#!/usr/bin/env python3
"""
Script para inicializar datos de prueba
"""
from app.db import SessionLocal, engine, Base
from app.models import User, Condominium, Unit
from app.auth import get_password_hash
import uuid

# Crear todas las tablas
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    # Crear condominio de prueba
    condominium = Condominium(
        id=uuid.uuid4(),
        name="Condominio Prueba",
        address="Calle Prueba 123",
        subscription_plan="small",
        subscription_status="active"
    )
    db.add(condominium)
    db.commit()
    db.refresh(condominium)
    print(f"✅ Condominio creado: {condominium.id}")

    # Crear unidad de prueba
    unit = Unit(
        id=uuid.uuid4(),
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

    # Crear usuario admin
    admin = User(
        id=uuid.uuid4(),
        email="admin@condosmart.com",
        password_hash=get_password_hash("admin123"),
        full_name="Administrador",
        role="admin",
        condominium_id=condominium.id,
        is_active=True
    )
    db.add(admin)
    db.commit()
    print("✅ Usuario admin creado: admin@condosmart.com / admin123")

    # Crear usuario residente
    resident = User(
        id=uuid.uuid4(),
        email="residente@condosmart.com",
        password_hash=get_password_hash("test123"),
        full_name="Usuario Residente",
        role="resident",
        condominium_id=condominium.id,
        unit_id=unit.id,
        is_active=True
    )
    db.add(resident)
    db.commit()
    print("✅ Usuario residente creado: residente@condosmart.com / test123")

    print("\n✅ Datos de prueba inicializados correctamente!")
    print(f"\n📝 Credenciales:")
    print(f"   Admin: admin@condosmart.com / admin123")
    print(f"   Residente: residente@condosmart.com / test123")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()

