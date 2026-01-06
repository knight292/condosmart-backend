#!/usr/bin/env python3
"""
Script para verificar qué base de datos está usando Railway
"""
import os
import sys

# Agregar el directorio app al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.db import DATABASE_URL, engine
from app.models.uuid_helper import USE_SQLITE

print("=" * 60)
print("  VERIFICACIÓN DE BASE DE DATOS")
print("=" * 60)
print()

# Verificar DATABASE_URL
print(f"📋 DATABASE_URL configurado:")
if DATABASE_URL:
    # Ocultar contraseña por seguridad
    safe_url = DATABASE_URL
    if '@' in safe_url:
        parts = safe_url.split('@')
        if ':' in parts[0]:
            user_pass = parts[0].split('://')[1] if '://' in parts[0] else parts[0]
            if ':' in user_pass:
                user = user_pass.split(':')[0]
                safe_url = safe_url.replace(user_pass, f"{user}:***")
    print(f"   {safe_url}")
else:
    print("   ❌ No configurado")
print()

# Verificar tipo de base de datos
print(f"📋 Tipo de base de datos:")
if USE_SQLITE:
    print("   ❌ SQLite (NO persistente - se borra en cada deploy)")
    print("   ⚠️  ADVERTENCIA: Los datos se perderán en cada deploy")
else:
    print("   ✅ PostgreSQL (PERSISTENTE - los datos se guardan)")
print()

# Intentar conectar
print("📋 Verificando conexión...")
try:
    with engine.connect() as conn:
        print("   ✅ Conexión exitosa")
        
        # Verificar si es PostgreSQL
        if not USE_SQLITE:
            result = conn.execute("SELECT version();")
            version = result.fetchone()[0]
            print(f"   📋 Versión: {version[:50]}...")
        else:
            print("   📋 SQLite detectado")
except Exception as e:
    print(f"   ❌ Error de conexión: {e}")
print()

# Verificar usuarios existentes
print("📋 Verificando usuarios en la base de datos...")
try:
    from app.db import SessionLocal
    from app.models import User
    
    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        print(f"   ✅ Usuarios encontrados: {user_count}")
        
        if user_count > 0:
            users = db.query(User.email, User.role).limit(5).all()
            print("   📋 Primeros usuarios:")
            for email, role in users:
                print(f"      - {email} ({role})")
    finally:
        db.close()
except Exception as e:
    print(f"   ⚠️  Error al verificar usuarios: {e}")
print()

print("=" * 60)
if USE_SQLITE:
    print("⚠️  ACCIÓN REQUERIDA: Configura PostgreSQL en Railway")
else:
    print("✅ Base de datos configurada correctamente (PostgreSQL)")
print("=" * 60)
