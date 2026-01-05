#!/usr/bin/env python3
"""
Script para crear usuarios de prueba con datos completos para probar métodos de pago
Incluye: condominio, unidades, admin, residente, métodos de pago y pagos pendientes
"""
from app.db import SessionLocal, engine, Base
from app.models import (
    User, Condominium, Unit, PaymentMethod, Payment
)
from app.auth import get_password_hash
from datetime import date, datetime, timedelta
import uuid

# Crear todas las tablas
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    print("🚀 Creando datos de prueba para métodos de pago...\n")
    
    # 1. Crear o obtener condominio
    print("1️⃣ Creando condominio...")
    condominium = db.query(Condominium).filter(Condominium.name == "Residencial Las Palmas").first()
    
    if not condominium:
        condominium = Condominium(
            id=uuid.uuid4(),
            name="Residencial Las Palmas",
            address="Av. Principal 456, Ciudad de México",
            subscription_plan="medium",
            subscription_status="active"
        )
        db.add(condominium)
        db.commit()
        db.refresh(condominium)
        print(f"   ✅ Condominio creado: {condominium.name}")
    else:
        print(f"   ✅ Condominio ya existe: {condominium.name}")
    
    # 2. Crear unidades
    print("\n2️⃣ Creando unidades...")
    unit_101 = db.query(Unit).filter(
        Unit.condominium_id == condominium.id,
        Unit.number == "101"
    ).first()
    
    if not unit_101:
        unit_101 = Unit(
            id=uuid.uuid4(),
            condominium_id=condominium.id,
            number="101",
            tower="Torre A",
            floor=1,
            type="apartment"
        )
        db.add(unit_101)
        db.commit()
        db.refresh(unit_101)
        print(f"   ✅ Unidad creada: Torre A - 101")
    else:
        print(f"   ✅ Unidad ya existe: Torre A - 101")
    
    unit_202 = db.query(Unit).filter(
        Unit.condominium_id == condominium.id,
        Unit.number == "202"
    ).first()
    
    if not unit_202:
        unit_202 = Unit(
            id=uuid.uuid4(),
            condominium_id=condominium.id,
            number="202",
            tower="Torre B",
            floor=2,
            type="apartment"
        )
        db.add(unit_202)
        db.commit()
        db.refresh(unit_202)
        print(f"   ✅ Unidad creada: Torre B - 202")
    else:
        print(f"   ✅ Unidad ya existe: Torre B - 202")
    
    # 3. Crear administrador
    print("\n3️⃣ Creando administrador...")
    admin_email = "admin@condosmart.com"
    admin = db.query(User).filter(User.email == admin_email).first()
    
    if not admin:
        admin = User(
            id=uuid.uuid4(),
            email=admin_email,
            password_hash=get_password_hash("admin123"),
            full_name="Administrador Principal",
            phone="+52 55 1234 5678",
            role="admin",
            condominium_id=condominium.id,
            is_active=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print(f"   ✅ Administrador creado: {admin_email}")
    else:
        # Actualizar condominio si no tiene
        if not admin.condominium_id:
            admin.condominium_id = condominium.id
            db.commit()
        print(f"   ✅ Administrador ya existe: {admin_email}")
    
    # 4. Crear residente
    print("\n4️⃣ Creando residente...")
    resident_email = "juan.perez@test.com"
    resident = db.query(User).filter(User.email == resident_email).first()
    
    if not resident:
        resident = User(
            id=uuid.uuid4(),
            email=resident_email,
            password_hash=get_password_hash("test123"),
            full_name="Juan Pérez",
            phone="+52 55 9876 5432",
            role="resident",
            condominium_id=condominium.id,
            unit_id=unit_101.id,
            is_active=True
        )
        db.add(resident)
        db.commit()
        db.refresh(resident)
        print(f"   ✅ Residente creado: {resident_email}")
    else:
        # Actualizar condominio y unidad si no tiene
        if not resident.condominium_id:
            resident.condominium_id = condominium.id
        if not resident.unit_id:
            resident.unit_id = unit_101.id
        db.commit()
        print(f"   ✅ Residente ya existe: {resident_email}")
    
    # 5. Crear métodos de pago
    print("\n5️⃣ Creando métodos de pago...")
    
    # Método 1: Depósito Bancario BBVA
    method_bbva = db.query(PaymentMethod).filter(
        PaymentMethod.condominium_id == condominium.id,
        PaymentMethod.name == "Depósito BBVA"
    ).first()
    
    if not method_bbva:
        method_bbva = PaymentMethod(
            id=uuid.uuid4(),
            condominium_id=condominium.id,
            method_type="bank_deposit",
            name="Depósito BBVA",
            bank_name="BBVA Bancomer",
            account_number="0123456789",
            clabe="012345678901234567",
            account_holder="Residencial Las Palmas A.C.",
            instructions="Realiza el depósito en cualquier sucursal BBVA o cajero automático. Sube el comprobante después de realizar el pago.",
            requires_verification=True,
            is_active=True
        )
        db.add(method_bbva)
        db.commit()
        print("   ✅ Método creado: Depósito BBVA")
    else:
        print("   ✅ Método ya existe: Depósito BBVA")
    
    # Método 2: Transferencia SPEI
    method_spei = db.query(PaymentMethod).filter(
        PaymentMethod.condominium_id == condominium.id,
        PaymentMethod.name == "Transferencia SPEI"
    ).first()
    
    if not method_spei:
        method_spei = PaymentMethod(
            id=uuid.uuid4(),
            condominium_id=condominium.id,
            method_type="spei",
            name="Transferencia SPEI",
            bank_name="Banorte",
            account_number="9876543210",
            clabe="072180001234567890",
            account_holder="Residencial Las Palmas A.C.",
            instructions="Realiza una transferencia SPEI desde tu banca en línea o app bancaria. El administrador verificará el pago cuando se reciba.",
            requires_verification=True,  # SPEI requiere verificación manual
            is_active=True
        )
        db.add(method_spei)
        db.commit()
        print("   ✅ Método creado: Transferencia SPEI")
    else:
        print("   ✅ Método ya existe: Transferencia SPEI")
    
    # Método 3: Oxxo Pay (inactivo de ejemplo)
    method_oxxo = db.query(PaymentMethod).filter(
        PaymentMethod.condominium_id == condominium.id,
        PaymentMethod.name == "Oxxo Pay"
    ).first()
    
    if not method_oxxo:
        method_oxxo = PaymentMethod(
            id=uuid.uuid4(),
            condominium_id=condominium.id,
            method_type="oxxo",
            name="Oxxo Pay",
            gateway_name="mercadopago",
            instructions="Paga en cualquier tienda Oxxo con el código que se generará.",
            requires_verification=False,
            is_active=False  # Inactivo para mostrar que los residentes no lo ven
        )
        db.add(method_oxxo)
        db.commit()
        print("   ✅ Método creado: Oxxo Pay (inactivo)")
    else:
        print("   ✅ Método ya existe: Oxxo Pay")
    
    # 6. Crear pagos pendientes para el residente
    print("\n6️⃣ Creando pagos pendientes...")
    
    # Verificar si ya tiene pagos
    existing_payment = db.query(Payment).filter(
        Payment.user_id == resident.id,
        Payment.status == "pending"
    ).first()
    
    if not existing_payment:
        # Pago pendiente de este mes
        payment1 = Payment(
            id=uuid.uuid4(),
            user_id=resident.id,
            condominium_id=condominium.id,
            amount=2500.00,
            currency="MXN",
            status="pending",
            due_date=date.today() + timedelta(days=5),
            payment_method=None
        )
        db.add(payment1)
        
        # Pago pendiente del mes pasado (vencido)
        payment2 = Payment(
            id=uuid.uuid4(),
            user_id=resident.id,
            condominium_id=condominium.id,
            amount=2500.00,
            currency="MXN",
            status="pending",
            due_date=date.today() - timedelta(days=10),
            payment_method=None
        )
        db.add(payment2)
        
        # Pago pagado de ejemplo
        payment3 = Payment(
            id=uuid.uuid4(),
            user_id=resident.id,
            condominium_id=condominium.id,
            amount=2500.00,
            currency="MXN",
            status="completed",
            due_date=date.today() - timedelta(days=40),
            payment_method="bank_deposit",
            paid_at=datetime.utcnow() - timedelta(days=35)
        )
        db.add(payment3)
        
        db.commit()
        print("   ✅ 3 pagos creados (2 pendientes, 1 pagado)")
    else:
        print("   ✅ Pagos ya existen para el residente")
    
    print("\n" + "="*60)
    print("✅ DATOS DE PRUEBA CREADOS EXITOSAMENTE!")
    print("="*60)
    print("\n📝 CREDENCIALES PARA PROBAR:")
    print("\n👨‍💼 ADMINISTRADOR:")
    print(f"   Email: {admin_email}")
    print(f"   Password: admin123")
    print(f"   Puede: Configurar métodos de pago, ver todos los pagos")
    
    print("\n👤 RESIDENTE:")
    print(f"   Email: {resident_email}")
    print(f"   Password: test123")
    print(f"   Unidad: Torre A - 101")
    print(f"   Puede: Ver sus pagos, pagar con métodos configurados")
    
    print("\n💰 MÉTODOS DE PAGO CONFIGURADOS:")
    print("   1. Depósito BBVA (Activo)")
    print("      - Banco: BBVA Bancomer")
    print("      - Cuenta: 0123456789")
    print("      - CLABE: 012345678901234567")
    print("      - Requiere verificación manual")
    
    print("\n   2. Transferencia SPEI (Activo)")
    print("      - Banco: Banorte")
    print("      - Cuenta: 9876543210")
    print("      - CLABE: 072180001234567890")
    print("      - Verificación automática")
    
    print("\n   3. Oxxo Pay (Inactivo - no visible para residentes)")
    
    print("\n💳 PAGOS CREADOS:")
    print("   - 2 pagos pendientes (uno vencido)")
    print("   - 1 pago completado (ejemplo)")
    
    print("\n🎯 PRÓXIMOS PASOS:")
    print("   1. Inicia sesión como administrador")
    print("   2. Ve a Pagos → Configuración (icono ⚙️)")
    print("   3. Verifica que los métodos estén configurados")
    print("   4. Inicia sesión como residente")
    print("   5. Ve a Pagos y toca 'Pagar' en un pago pendiente")
    print("   6. Deberías ver los métodos activos (BBVA y SPEI)")
    
    print("\n" + "="*60)

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()

