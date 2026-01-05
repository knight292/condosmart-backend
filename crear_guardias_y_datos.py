#!/usr/bin/env python3
"""
Script para crear múltiples guardias y datos ficticios para pruebas
"""
from app.db import SessionLocal, engine, Base
from app.models import (
    User, Condominium, GuardShift, Package
)
from app.auth import get_password_hash
import uuid
from datetime import datetime, timedelta
import random

# Crear todas las tablas
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    print("🎯 Creando guardias y datos ficticios...")
    print("")
    
    # 1. Obtener o crear condominio
    print("1️⃣  Obteniendo condominio...")
    condominium = db.query(Condominium).first()
    if not condominium:
        condominium = Condominium(
            id=uuid.uuid4(),
            name="Residencial Las Palmas",
            address="Av. Principal 123, Ciudad",
            subscription_plan="medium",
            subscription_status="active"
        )
        db.add(condominium)
        db.commit()
        db.refresh(condominium)
        print(f"   ✅ Condominio creado: {condominium.name}")
    else:
        print(f"   ✅ Condominio encontrado: {condominium.name}")
    
    # 2. Crear múltiples guardias
    print("2️⃣  Creando guardias...")
    guardias_data = [
        ("Roberto Sánchez", "guardia1@condosmart.com", "guard123"),
        ("Carlos Mendoza", "guardia2@condosmart.com", "guard123"),
        ("Miguel Torres", "guardia3@condosmart.com", "guard123"),
        ("José Ramírez", "guardia4@condosmart.com", "guard123"),
        ("Fernando López", "guardia5@condosmart.com", "guard123"),
    ]
    
    guards = []
    for nombre, email, password in guardias_data:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            if existing.role != "guard":
                existing.role = "guard"
                existing.condominium_id = condominium.id
                existing.password_hash = get_password_hash(password)
                db.commit()
            guards.append(existing)
            print(f"   ✅ Guardia actualizado: {email}")
        else:
            guard = User(
                id=uuid.uuid4(),
                email=email,
                password_hash=get_password_hash(password),
                full_name=nombre,
                phone=f"555{3000 + len(guards)}",
                role="guard",
                condominium_id=condominium.id,
                is_active=True
            )
            db.add(guard)
            guards.append(guard)
            print(f"   ✅ Guardia creado: {email} / {password}")
    db.commit()
    print(f"   ✅ Total: {len(guards)} guardias listos")
    
    # 3. Crear turnos (shifts) para los guardias
    print("3️⃣  Creando turnos de guardias...")
    shift_types = ["morning", "afternoon", "night", "full_day"]
    statuses = ["scheduled", "active", "completed"]
    
    shifts_created = 0
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Turnos pasados (completados)
    for i in range(-7, 0):  # Últimos 7 días
        for guard in guards:
            shift_date = today + timedelta(days=i)
            shift_type = random.choice(shift_types)
            
            # Determinar horas según el tipo de turno
            if shift_type == "morning":
                shift_start = shift_date.replace(hour=6, minute=0)
                shift_end = shift_date.replace(hour=14, minute=0)
            elif shift_type == "afternoon":
                shift_start = shift_date.replace(hour=14, minute=0)
                shift_end = shift_date.replace(hour=22, minute=0)
            elif shift_type == "night":
                shift_start = shift_date.replace(hour=22, minute=0)
                shift_end = (shift_date + timedelta(days=1)).replace(hour=6, minute=0)
            else:  # full_day
                shift_start = shift_date.replace(hour=6, minute=0)
                shift_end = shift_date.replace(hour=22, minute=0)
            
            status = "completed"
            check_in = shift_start + timedelta(minutes=random.randint(0, 30))
            check_out = shift_end - timedelta(minutes=random.randint(0, 30))
            
            shift = GuardShift(
                id=uuid.uuid4(),
                condominium_id=condominium.id,
                guard_id=guard.id,
                shift_date=shift_start,
                shift_type=shift_type,
                status=status,
                check_in_time=check_in,
                check_out_time=check_out,
                notes=f"Turno {shift_type} completado normalmente"
            )
            db.add(shift)
            shifts_created += 1
    
    # Turnos de hoy (algunos activos, algunos programados)
    for guard in guards[:2]:  # Solo los primeros 2 guardias tienen turno hoy
        shift_date = today
        shift_type = random.choice(shift_types[:3])  # No full_day hoy
        
        if shift_type == "morning":
            shift_start = shift_date.replace(hour=6, minute=0)
            shift_end = shift_date.replace(hour=14, minute=0)
        elif shift_type == "afternoon":
            shift_start = shift_date.replace(hour=14, minute=0)
            shift_end = shift_date.replace(hour=22, minute=0)
        else:  # night
            shift_start = shift_date.replace(hour=22, minute=0)
            shift_end = (shift_date + timedelta(days=1)).replace(hour=6, minute=0)
        
        # Si el turno ya pasó, está completado; si está en curso, activo; si es futuro, programado
        now = datetime.now()
        if now > shift_end:
            status = "completed"
            check_in = shift_start + timedelta(minutes=5)
            check_out = shift_end - timedelta(minutes=5)
        elif now >= shift_start:
            status = "active"
            check_in = shift_start + timedelta(minutes=5)
            check_out = None
        else:
            status = "scheduled"
            check_in = None
            check_out = None
        
        shift = GuardShift(
            id=uuid.uuid4(),
            condominium_id=condominium.id,
            guard_id=guard.id,
            shift_date=shift_start,
            shift_type=shift_type,
            status=status,
            check_in_time=check_in,
            check_out_time=check_out,
            notes=None
        )
        db.add(shift)
        shifts_created += 1
    
    # Turnos futuros (programados)
    for i in range(1, 8):  # Próximos 7 días
        for guard in guards:
            if random.random() > 0.7:  # 30% de probabilidad de tener turno
                shift_date = today + timedelta(days=i)
                shift_type = random.choice(shift_types)
                
                if shift_type == "morning":
                    shift_start = shift_date.replace(hour=6, minute=0)
                    shift_end = shift_date.replace(hour=14, minute=0)
                elif shift_type == "afternoon":
                    shift_start = shift_date.replace(hour=14, minute=0)
                    shift_end = shift_date.replace(hour=22, minute=0)
                elif shift_type == "night":
                    shift_start = shift_date.replace(hour=22, minute=0)
                    shift_end = (shift_date + timedelta(days=1)).replace(hour=6, minute=0)
                else:  # full_day
                    shift_start = shift_date.replace(hour=6, minute=0)
                    shift_end = shift_date.replace(hour=22, minute=0)
                
                shift = GuardShift(
                    id=uuid.uuid4(),
                    condominium_id=condominium.id,
                    guard_id=guard.id,
                    shift_date=shift_start,
                    shift_type=shift_type,
                    status="scheduled",
                    notes=None
                )
                db.add(shift)
                shifts_created += 1
    
    db.commit()
    print(f"   ✅ {shifts_created} turnos creados")
    
    # 4. Obtener residentes para crear paquetes
    print("4️⃣  Creando paquetes...")
    residents = db.query(User).filter(User.role == "resident", User.condominium_id == condominium.id).limit(5).all()
    
    if residents:
        carriers = ["DHL", "FedEx", "UPS", "Correos de México", "Estafeta"]
        package_statuses = ["pending", "delivered", "picked_up"]
        
        packages_created = 0
        for i in range(15):  # Crear 15 paquetes
            resident = random.choice(residents)
            guard = random.choice(guards)
            carrier = random.choice(carriers)
            status = random.choice(package_statuses)
            
            # Fechas aleatorias en los últimos 10 días
            days_ago = random.randint(0, 10)
            created_at = datetime.now() - timedelta(days=days_ago)
            
            package = Package(
                id=uuid.uuid4(),
                condominium_id=condominium.id,
                resident_id=resident.id,
                received_by_id=guard.id,
                carrier=carrier,
                tracking_number=f"TRK{random.randint(100000, 999999)}",
                description=f"Paquete {i+1} de {carrier}",
                notes=f"Paquete registrado por {guard.full_name}" if random.random() > 0.5 else None,
                status=status,
                received_at=created_at,
                created_at=created_at
            )
            db.add(package)
            packages_created += 1
        
        db.commit()
        print(f"   ✅ {packages_created} paquetes creados")
    else:
        print("   ⚠️  No hay residentes para asignar paquetes")
    
    print("")
    print("=" * 60)
    print("✅ GUARDIAS Y DATOS FICTICIOS CREADOS EXITOSAMENTE")
    print("=" * 60)
    print("")
    print("👤 CREDENCIALES DE GUARDIAS:")
    print("")
    for guard in guards:
        print(f"   • {guard.full_name}")
        print(f"     Email: {guard.email}")
        print(f"     Password: guard123")
        print("")
    
    print("📊 DATOS GENERADOS:")
    print(f"   • {len(guards)} Guardias")
    print(f"   • {shifts_created} Turnos de guardias")
    if residents:
        print(f"   • 15 Paquetes")
    print("")
    print("🎯 Ahora puedes:")
    print("   1. Iniciar sesión con cualquier guardia")
    print("   2. Ver sus turnos en 'Mis Turnos'")
    print("   3. Ver paquetes pendientes en el dashboard")
    print("   4. Registrar nuevos paquetes")
    print("")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()

