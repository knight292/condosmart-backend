#!/usr/bin/env python3
"""
Script para crear paquetes ficticios
"""
from app.db import SessionLocal
from app.models import User, Package, Condominium
import uuid
from datetime import datetime, timedelta
import random

db = SessionLocal()

try:
    print("🎯 Creando paquetes ficticios...")
    
    # Obtener residentes primero para encontrar su condominio
    residents = db.query(User).filter(
        User.role == "resident",
        User.condominium_id.isnot(None)
    ).all()
    
    if not residents:
        print("❌ No hay residentes con condominio asignado")
        exit(1)
    
    # Usar el condominio del primer residente
    condominium_id = residents[0].condominium_id
    condominium = db.query(Condominium).filter(Condominium.id == condominium_id).first()
    
    if not condominium:
        print("❌ No se encontró el condominio")
        exit(1)
    
    print(f"✅ Usando condominio: {condominium.name}")
    
    # Filtrar residentes del mismo condominio
    residents = [r for r in residents if r.condominium_id == condominium_id]
    
    # Obtener guardias del mismo condominio o moverlos
    guards = db.query(User).filter(
        User.role == "guard",
        User.condominium_id == condominium_id
    ).all()
    
    # Si no hay guardias en este condominio, mover algunos
    if not guards:
        print("⚠️  No hay guardias en este condominio, moviendo algunos...")
        all_guards = db.query(User).filter(User.role == "guard").limit(3).all()
        for guard in all_guards:
            guard.condominium_id = condominium_id
            guards.append(guard)
        db.commit()
        print(f"✅ {len(guards)} guardias movidos al condominio")
    
    if not guards:
        print("❌ No hay guardias")
        exit(1)
    
    carriers = ["DHL", "FedEx", "UPS", "Correos de México", "Estafeta"]
    package_statuses = ["pending", "received", "picked_up"]
    
    packages_created = 0
    for i in range(20):  # Crear 20 paquetes
        resident = random.choice(residents)
        guard = random.choice(guards)
        carrier = random.choice(carriers)
        status = random.choice(package_statuses)
        
        # Fechas aleatorias en los últimos 15 días
        days_ago = random.randint(0, 15)
        created_at = datetime.now() - timedelta(days=days_ago)
        
        package = Package(
            id=uuid.uuid4(),
            condominium_id=condominium.id,
            resident_id=resident.id,
            received_by_id=guard.id,
            carrier=carrier,
            tracking_number=f"TRK{random.randint(100000, 999999)}",
            description=f"Paquete {i+1} de {carrier} para {resident.full_name}",
            notes=f"Paquete registrado por {guard.full_name}" if random.random() > 0.5 else None,
            status=status,
            received_at=created_at,
            created_at=created_at
        )
        
        if status == "picked_up":
            package.picked_up_at = created_at + timedelta(days=random.randint(1, 5))
        
        db.add(package)
        packages_created += 1
    
    db.commit()
    print(f"✅ {packages_created} paquetes creados")
    print(f"   • Residentes: {len(residents)}")
    print(f"   • Guardias: {len(guards)}")
    print(f"   • Condominio: {condominium.name}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()

