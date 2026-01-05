#!/usr/bin/env python3
"""
Script para crear un owner de ejemplo y asignarle condominios
"""
from app.db import SessionLocal, engine, Base
from app.models import Owner, User, Condominium
from app.auth import get_password_hash
import uuid

# Crear todas las tablas
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    # Verificar si el owner ya existe
    existing_owner = db.query(Owner).filter(Owner.email == "owner@condosmart.com").first()
    if existing_owner:
        owner = existing_owner
        print(f"✅ Owner ya existe: {owner.id} - {owner.name}")
    else:
        # Crear owner
        owner = Owner(
            id=uuid.uuid4(),
            name="Empresa de Administración de Condominios S.A.",
            email="owner@condosmart.com",
            phone="+52 55 1234 5678",
            address="Av. Principal 123, Ciudad de México",
            tax_id="ABC123456789",
            is_active="active"
        )
        db.add(owner)
        db.commit()
        db.refresh(owner)
        print(f"✅ Owner creado: {owner.id} - {owner.name}")

    # Verificar si el usuario owner ya existe
    existing_user = db.query(User).filter(User.email == "owner@condosmart.com").first()
    if existing_user:
        if existing_user.owner_id != owner.id:
            existing_user.owner_id = owner.id
            db.commit()
        print(f"✅ Usuario owner ya existe: {existing_user.email} / owner123")
    else:
        # Crear usuario owner
        owner_user = User(
            id=uuid.uuid4(),
            email="owner@condosmart.com",
            password_hash=get_password_hash("owner123"),
            full_name="Administrador General",
            role="owner",
            owner_id=owner.id,
            is_active=True
        )
        db.add(owner_user)
        db.commit()
        print(f"✅ Usuario owner creado: {owner_user.email} / owner123")

    # Asignar condominios existentes al owner (opcional)
    # Esto asigna todos los condominios existentes al owner
    condominiums = db.query(Condominium).all()
    for condo in condominiums:
        condo.owner_id = owner.id
        db.commit()
        print(f"✅ Condominio '{condo.name}' asignado al owner")

    print("\n✅ Setup completado!")
    print(f"\n📝 Credenciales Owner:")
    print(f"   Email: owner@condosmart.com")
    print(f"   Password: owner123")
    print(f"\n📊 Condominios asignados: {len(condominiums)}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()

