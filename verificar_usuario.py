#!/usr/bin/env python3
"""
Script rápido para verificar si un usuario existe y crear uno si no existe
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import SessionLocal
from app.models import User, Condominium, Unit
from app.auth import get_password_hash, verify_password
import uuid

db = SessionLocal()

try:
    email = "juan.perez@test.com"
    password = "test123"
    
    print(f"🔍 Buscando usuario: {email}")
    
    user = db.query(User).filter(User.email == email).first()
    
    if user:
        print(f"✅ Usuario encontrado: {user.full_name}")
        print(f"   Role: {user.role}")
        print(f"   Condominio: {user.condominium_id}")
        print(f"   Unidad: {user.unit_id}")
        print(f"   Activo: {user.is_active}")
        
        # Verificar contraseña
        if verify_password(password, user.password_hash):
            print(f"✅ Contraseña correcta")
        else:
            print(f"⚠️  Contraseña NO coincide")
            print(f"   Actualizando contraseña...")
            user.password_hash = get_password_hash(password)
            db.commit()
            print(f"✅ Contraseña actualizada")
    else:
        print(f"❌ Usuario NO existe")
        print(f"   Creando usuario...")
        
        # Buscar o crear condominio
        condo = db.query(Condominium).first()
        if not condo:
            condo = Condominium(
                id=uuid.uuid4(),
                name="Residencial Las Palmas",
                address="Av. Principal 456",
                subscription_plan="medium",
                subscription_status="active"
            )
            db.add(condo)
            db.commit()
            db.refresh(condo)
            print(f"   ✅ Condominio creado: {condo.name}")
        
        # Buscar o crear unidad
        unit = db.query(Unit).filter(Unit.condominium_id == condo.id).first()
        if not unit:
            unit = Unit(
                id=uuid.uuid4(),
                condominium_id=condo.id,
                number="101",
                tower="Torre A",
                floor=1,
                type="apartment"
            )
            db.add(unit)
            db.commit()
            db.refresh(unit)
            print(f"   ✅ Unidad creada: Torre A - 101")
        
        # Crear usuario
        user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash=get_password_hash(password),
            full_name="Juan Pérez",
            phone="+52 55 9876 5432",
            role="resident",
            condominium_id=condo.id,
            unit_id=unit.id,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✅ Usuario creado: {user.email}")
    
    print(f"\n📝 Credenciales:")
    print(f"   Email: {email}")
    print(f"   Password: {password}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()

