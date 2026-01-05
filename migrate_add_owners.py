#!/usr/bin/env python3
"""
Script de migración para agregar soporte de owners
Agrega las columnas owner_id a users y condominiums
"""
import sqlite3
import os

DB_PATH = "test_condosmart.db"

if not os.path.exists(DB_PATH):
    print(f"❌ Base de datos {DB_PATH} no encontrada")
    exit(1)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    # Verificar si las columnas ya existen
    cursor.execute("PRAGMA table_info(users)")
    users_columns = [col[1] for col in cursor.fetchall()]
    
    cursor.execute("PRAGMA table_info(condominiums)")
    condos_columns = [col[1] for col in cursor.fetchall()]
    
    # Agregar owner_id a users si no existe
    if 'owner_id' not in users_columns:
        print("📝 Agregando columna owner_id a tabla users...")
        cursor.execute("ALTER TABLE users ADD COLUMN owner_id TEXT")
        print("✅ Columna owner_id agregada a users")
    else:
        print("✅ Columna owner_id ya existe en users")
    
    # Agregar owner_id a condominiums si no existe
    if 'owner_id' not in condos_columns:
        print("📝 Agregando columna owner_id a tabla condominiums...")
        cursor.execute("ALTER TABLE condominiums ADD COLUMN owner_id TEXT")
        print("✅ Columna owner_id agregada a condominiums")
    else:
        print("✅ Columna owner_id ya existe en condominiums")
    
    # Verificar si la tabla owners existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='owners'")
    if cursor.fetchone() is None:
        print("📝 Creando tabla owners...")
        cursor.execute("""
            CREATE TABLE owners (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                address TEXT,
                tax_id TEXT,
                is_active TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Tabla owners creada")
    else:
        print("✅ Tabla owners ya existe")
    
    conn.commit()
    print("\n✅ Migración completada exitosamente!")
    
except Exception as e:
    print(f"❌ Error en la migración: {e}")
    conn.rollback()
finally:
    conn.close()

