#!/usr/bin/env python3
"""
Script para verificar que todas las tablas estén creadas en PostgreSQL
"""
import os
import sys

# Agregar el directorio app al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.db import engine, Base
from sqlalchemy import inspect

print("=" * 60)
print("  VERIFICACIÓN DE TABLAS EN BASE DE DATOS")
print("=" * 60)
print()

# Obtener inspector de SQLAlchemy
inspector = inspect(engine)

# Obtener todas las tablas existentes
existing_tables = inspector.get_table_names()

print(f"📋 Tablas encontradas en la base de datos: {len(existing_tables)}")
print()

# Lista de tablas esperadas (basadas en los modelos - nombres reales)
expected_tables = [
    'users',
    'condominiums',
    'units',
    'payments',
    'payment_methods',
    'maintenance_tickets',  # El nombre real es maintenance_tickets, no tickets
    'ticket_attachments',
    'visits',
    'reservations',
    'announcements',
    'messages',
    'documents',
    'maintenances',
    'contracts',
    'inventory_items',
    'regulations',
    'guard_shifts',
    'guard_availabilities',  # El nombre real es guard_availabilities (plural)
    'shift_templates',
    'shift_swaps',
    'packages',
    'licenses',
    'recurring_payments',
    'owners',
]

print("📋 Tablas esperadas vs encontradas:")
print()

missing_tables = []
for table in expected_tables:
    if table in existing_tables:
        print(f"   ✅ {table}")
    else:
        print(f"   ❌ {table} - FALTA")
        missing_tables.append(table)

print()

# Mostrar tablas adicionales (si las hay)
extra_tables = [t for t in existing_tables if t not in expected_tables]
if extra_tables:
    print("📋 Tablas adicionales encontradas:")
    for table in extra_tables:
        print(f"   ℹ️  {table}")
    print()

# Resumen
print("=" * 60)
if missing_tables:
    print(f"⚠️  FALTAN {len(missing_tables)} TABLAS:")
    for table in missing_tables:
        print(f"   - {table}")
    print()
    print("💡 Las tablas se crearán automáticamente en el próximo reinicio")
    print("   o puedes forzar la creación ejecutando el servidor nuevamente")
else:
    print("✅ TODAS LAS TABLAS ESTÁN CREADAS")
    print(f"   Total: {len(existing_tables)} tablas")
print("=" * 60)
