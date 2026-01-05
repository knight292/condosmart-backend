#!/usr/bin/env python3
"""
Script para verificar datos existentes
"""
from app.db import SessionLocal
from app.models import User, Condominium, GuardShift, Package

db = SessionLocal()

try:
    print("📊 Verificando datos...")
    print("")
    
    # Condominios
    condominiums = db.query(Condominium).all()
    print(f"Condominios: {len(condominiums)}")
    for c in condominiums:
        print(f"  • {c.name} (ID: {c.id})")
    
    print("")
    
    # Usuarios por rol
    for role in ["admin", "resident", "guard"]:
        users = db.query(User).filter(User.role == role).all()
        print(f"{role.capitalize()}s: {len(users)}")
        for u in users[:5]:
            print(f"  • {u.full_name} ({u.email}) - Condo: {u.condominium_id}")
    
    print("")
    
    # Turnos
    shifts = db.query(GuardShift).all()
    print(f"Turnos de guardias: {len(shifts)}")
    
    # Paquetes
    packages = db.query(Package).all()
    print(f"Paquetes: {len(packages)}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()

