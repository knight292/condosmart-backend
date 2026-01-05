#!/usr/bin/env python3
"""
Script para generar datos de demostración
"""
from app.db import SessionLocal, engine, Base
from app.models import (
    User, Condominium, Unit, Payment, Ticket, TicketAttachment,
    Visit, Reservation, Announcement, Message
)
from app.auth import get_password_hash
import uuid
from datetime import datetime, timedelta
import random

# Crear todas las tablas
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    print("🎯 Generando datos de demostración...")
    print("")
    
    # 1. Crear Condominio
    print("1️⃣  Creando condominio...")
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
    
    # 2. Crear Unidades
    print("2️⃣  Creando unidades...")
    units = []
    towers = ["A", "B", "C"]
    for tower in towers:
        for floor in range(1, 6):
            for unit_num in range(1, 5):
                unit = Unit(
                    id=uuid.uuid4(),
                    condominium_id=condominium.id,
                    number=f"{tower}{floor}{unit_num:02d}",
                    tower=tower,
                    floor=floor,
                    type="apartment"
                )
                db.add(unit)
                units.append(unit)
    db.commit()
    print(f"   ✅ {len(units)} unidades creadas")
    
    # 3. Crear Usuario Administrador
    print("3️⃣  Creando usuario administrador...")
    existing_admin = db.query(User).filter(User.email == "admin@condosmart.com").first()
    if existing_admin:
        admin = existing_admin
        admin.condominium_id = condominium.id
        db.commit()
        print(f"   ✅ Admin ya existe: admin@condosmart.com / admin123")
    else:
        admin = User(
            id=uuid.uuid4(),
            email="admin@condosmart.com",
            password_hash=get_password_hash("admin123"),
            full_name="Administrador Principal",
            phone="5551234567",
            role="admin",
            condominium_id=condominium.id,
            is_active=True
        )
        db.add(admin)
        db.commit()
        print(f"   ✅ Admin creado: admin@condosmart.com / admin123")
    
    # 4. Crear Residentes
    print("4️⃣  Creando residentes...")
    residentes_nombres = [
        ("Juan Pérez", "juan@test.com"),
        ("María García", "maria@test.com"),
        ("Carlos López", "carlos@test.com"),
        ("Ana Martínez", "ana@test.com"),
        ("Luis Rodríguez", "luis@test.com"),
    ]
    
    residents = []
    for i, (nombre, email) in enumerate(residentes_nombres):
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            existing.condominium_id = condominium.id
            existing.unit_id = units[i].id if i < len(units) else None
            residents.append(existing)
        else:
            resident = User(
                id=uuid.uuid4(),
                email=email,
                password_hash=get_password_hash("test123"),
                full_name=nombre,
                phone=f"555{1000+i}",
                role="resident",
                condominium_id=condominium.id,
                unit_id=units[i].id if i < len(units) else None,
                is_active=True
            )
            db.add(resident)
            residents.append(resident)
    db.commit()
    print(f"   ✅ {len(residents)} residentes listos")
    
    # 5. Crear Pagos
    print("5️⃣  Creando pagos de mantenimiento...")
    for resident in residents:
        # Pago pendiente
        payment_pending = Payment(
            id=uuid.uuid4(),
            user_id=resident.id,
            condominium_id=condominium.id,
            amount=2500.00,
            currency="MXN",
            status="pending",
            payment_method=None,
            due_date=(datetime.now() + timedelta(days=5)).date(),
        )
        db.add(payment_pending)
        
        # Pago completado (mes pasado)
        payment_completed = Payment(
            id=uuid.uuid4(),
            user_id=resident.id,
            condominium_id=condominium.id,
            amount=2500.00,
            currency="MXN",
            status="completed",
            payment_method="card",
            payment_gateway="stripe",
            paid_at=datetime.now() - timedelta(days=30),
            due_date=(datetime.now() - timedelta(days=30)).date(),
        )
        db.add(payment_completed)
    db.commit()
    print(f"   ✅ Pagos creados")
    
    # 6. Crear Tickets
    print("6️⃣  Creando tickets de mantenimiento...")
    tickets_data = [
        ("Fuga de agua en baño", "Agua", "high", "new"),
        ("Luz fundida en pasillo", "Luz", "medium", "in_progress"),
        ("Basura acumulada", "Basura", "low", "resolved"),
        ("Puerta del elevador no cierra", "Otro", "high", "assigned"),
    ]
    
    for i, (titulo, categoria, prioridad, estado) in enumerate(tickets_data):
        ticket = Ticket(
            id=uuid.uuid4(),
            condominium_id=condominium.id,
            reported_by=residents[i % len(residents)].id,
            category=categoria,
            title=titulo,
            description=f"Descripción del problema: {titulo}",
            status=estado,
            priority=prioridad,
            assigned_to=admin.id if estado in ["assigned", "in_progress"] else None,
        )
        if estado == "resolved":
            ticket.resolved_at = datetime.now() - timedelta(days=2)
        db.add(ticket)
    db.commit()
    print(f"   ✅ Tickets creados")
    
    # 7. Crear Reservaciones
    print("7️⃣  Creando reservaciones...")
    facilities = ["Alberca", "Gimnasio", "Salón de Eventos", "Parrillas"]
    for i, facility in enumerate(facilities):
        reservation = Reservation(
            id=uuid.uuid4(),
            condominium_id=condominium.id,
            user_id=residents[i % len(residents)].id,
            unit_id=residents[i % len(residents)].unit_id,
            facility_type=facility,
            start_time=datetime.now() + timedelta(days=i+1, hours=10),
            end_time=datetime.now() + timedelta(days=i+1, hours=12),
            status="confirmed",
        )
        db.add(reservation)
    db.commit()
    print(f"   ✅ Reservaciones creadas")
    
    # 8. Crear Avisos
    print("8️⃣  Creando avisos y comunicados...")
    announcements_data = [
        ("Mantenimiento de elevador", "Mantenimiento programado mañana de 9am a 12pm", "maintenance", "high"),
        ("Fiesta Navideña", "Te invitamos a la fiesta de fin de año el 20 de diciembre", "event", "normal"),
        ("Recordatorio de pago", "Recuerda pagar tu mantenimiento antes del día 5", "announcement", "normal"),
    ]
    
    for titulo, contenido, categoria, prioridad in announcements_data:
        announcement = Announcement(
            id=uuid.uuid4(),
            condominium_id=condominium.id,
            created_by=admin.id,
            title=titulo,
            content=contenido,
            category=categoria,
            priority=prioridad,
            target_audience="all",
        )
        db.add(announcement)
    db.commit()
    print(f"   ✅ Avisos creados")
    
    # 9. Crear Visitas
    print("9️⃣  Creando visitas...")
    for i, resident in enumerate(residents[:3]):
        visit = Visit(
            id=uuid.uuid4(),
            condominium_id=condominium.id,
            unit_id=resident.unit_id,
            visitor_name=f"Visitante {i+1}",
            visitor_phone=f"555{2000+i}",
            qr_code=str(uuid.uuid4()),
            status="pending" if i == 0 else "checked_in" if i == 1 else "checked_out",
            valid_until=datetime.now() + timedelta(hours=8),
            entry_time=datetime.now() - timedelta(hours=2) if i > 0 else None,
            exit_time=datetime.now() - timedelta(hours=1) if i == 2 else None,
        )
        db.add(visit)
    db.commit()
    print(f"   ✅ Visitas creadas")
    
    print("")
    print("=" * 60)
    print("✅ DATOS DE DEMOSTRACIÓN CREADOS EXITOSAMENTE")
    print("=" * 60)
    print("")
    print("👤 CREDENCIALES:")
    print("")
    print("   ADMINISTRADOR:")
    print("   Email: admin@condosmart.com")
    print("   Password: admin123")
    print("")
    print("   RESIDENTES:")
    for resident in residents:
        print(f"   Email: {resident.email} | Password: test123")
    print("")
    print("📊 DATOS GENERADOS:")
    print(f"   • 1 Condominio")
    print(f"   • {len(units)} Unidades")
    print(f"   • 1 Administrador")
    print(f"   • {len(residents)} Residentes")
    print(f"   • {len(residents) * 2} Pagos")
    print(f"   • {len(tickets_data)} Tickets")
    print(f"   • {len(facilities)} Reservaciones")
    print(f"   • {len(announcements_data)} Avisos")
    print(f"   • 3 Visitas")
    print("")
    print("🎯 Ahora puedes:")
    print("   1. Login como admin: admin@condosmart.com / admin123")
    print("   2. Ver el dashboard con todos los datos")
    print("   3. Probar todas las funcionalidades")
    print("")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()

