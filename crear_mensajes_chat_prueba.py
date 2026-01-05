#!/usr/bin/env python3
"""
Script para crear mensajes de chat de prueba para el condominio
"""
from app.db import SessionLocal, engine, Base
from app.models import (
    User, Condominium, Message
)
from datetime import datetime, timedelta
import uuid

# Crear todas las tablas
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    print("🚀 Creando mensajes de chat de prueba...\n")
    
    # 1. Buscar el condominio "Residencial Las Palmas"
    print("1️⃣ Buscando condominio...")
    condominium = db.query(Condominium).filter(Condominium.name == "Residencial Las Palmas").first()
    
    if not condominium:
        print("   ❌ No se encontró el condominio 'Residencial Las Palmas'")
        print("   💡 Ejecuta primero: python crear_usuarios_prueba_pagos.py")
        exit(1)
    
    print(f"   ✅ Condominio encontrado: {condominium.name}")
    
    # 2. Buscar usuarios del condominio
    print("\n2️⃣ Buscando usuarios del condominio...")
    users = db.query(User).filter(
        User.condominium_id == condominium.id,
        User.is_active == True
    ).all()
    
    if len(users) < 1:
        print(f"   ❌ No se encontraron usuarios activos en el condominio")
        print("   💡 Ejecuta primero: python crear_usuarios_prueba_pagos.py")
        exit(1)
    
    print(f"   ✅ Encontrados {len(users)} usuarios:")
    for user in users:
        print(f"      - {user.full_name} ({user.email}) - {user.role}")
    
    # Si solo hay un usuario, usaremos ese para todos los mensajes
    if len(users) == 1:
        print("   ⚠️ Solo hay un usuario. Se crearán mensajes de ejemplo con ese usuario.")
    
    # 3. Verificar si ya hay mensajes
    existing_messages = db.query(Message).filter(
        Message.condominium_id == condominium.id,
        Message.conversation_type == "general"
    ).count()
    
    if existing_messages > 0:
        print(f"\n   ⚠️ Ya existen {existing_messages} mensajes en el chat")
        respuesta = input("   ¿Deseas agregar más mensajes? (s/n): ").lower()
        if respuesta != 's':
            print("   ✅ No se agregaron mensajes nuevos")
            exit(0)
    
    # 4. Crear mensajes de ejemplo
    print("\n3️⃣ Creando mensajes de chat de ejemplo...")
    
    # Seleccionar usuarios para los mensajes
    sender1 = users[0]
    sender2 = users[1] if len(users) > 1 else users[0]  # Si solo hay uno, usar el mismo
    
    mensajes_ejemplo = [
        {
            "content": "¡Hola a todos! 👋 Bienvenidos al chat del condominio.",
            "sender": sender1,
            "hours_ago": 48
        },
        {
            "content": "Hola! Gracias por la bienvenida. ¿Alguien sabe cuándo será la próxima junta?",
            "sender": sender2,
            "hours_ago": 45
        },
        {
            "content": "La próxima junta será el próximo viernes a las 7 PM en el salón de usos múltiples.",
            "sender": sender1,
            "hours_ago": 44
        },
        {
            "content": "Perfecto, gracias por la información!",
            "sender": sender2,
            "hours_ago": 43
        },
        {
            "content": "¿Alguien más tiene problemas con el elevador de la Torre A?",
            "sender": sender1,
            "hours_ago": 24
        },
        {
            "content": "Sí, yo también. Ya reporté el problema a la administración.",
            "sender": sender2,
            "hours_ago": 22
        },
        {
            "content": "Gracias por reportarlo. Ya están trabajando en ello.",
            "sender": sender1,
            "hours_ago": 20
        },
        {
            "content": "Recordatorio: El pago de mantenimiento vence el día 5 de cada mes. Por favor realicen su pago a tiempo.",
            "sender": sender1,
            "hours_ago": 12
        },
        {
            "content": "Entendido, gracias por el recordatorio!",
            "sender": sender2,
            "hours_ago": 10
        },
        {
            "content": "¡Buenos días a todos! Que tengan un excelente día 🌞",
            "sender": sender1,
            "hours_ago": 2
        }
    ]
    
    created_count = 0
    for msg_data in mensajes_ejemplo:
        # Crear mensaje con timestamp relativo
        created_at = datetime.utcnow() - timedelta(hours=msg_data["hours_ago"])
        
        message = Message(
            id=uuid.uuid4(),
            condominium_id=condominium.id,
            sender_id=msg_data["sender"].id,
            conversation_type="general",
            content=msg_data["content"],
            is_read=False,
            created_at=created_at
        )
        db.add(message)
        created_count += 1
    
    db.commit()
    print(f"   ✅ {created_count} mensajes de chat creados exitosamente")
    
    print("\n" + "="*60)
    print("✅ MENSAJES DE CHAT CREADOS EXITOSAMENTE!")
    print("="*60)
    print(f"\n📝 Total de mensajes en el chat: {existing_messages + created_count}")
    print("\n💬 Los mensajes incluyen:")
    print("   - Mensajes de bienvenida")
    print("   - Conversaciones sobre juntas")
    print("   - Reportes de problemas")
    print("   - Recordatorios de pagos")
    print("   - Mensajes recientes")
    print("\n🎯 Ahora puedes iniciar sesión y ver el historial de chat!")
    print("="*60)

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()

