#!/usr/bin/env python3
"""
Migración: agrega columna settings a condominiums (SQLite local o PostgreSQL).
Uso:
  python migrate_add_condominium_settings.py
  railway run python migrate_add_condominium_settings.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import inspect, text

from app.db import engine, SessionLocal
from app.models import Condominium
from app.models.uuid_helper import USE_SQLITE
from app.services.condominium_settings import apply_default_settings


def ensure_settings_column() -> bool:
    inspector = inspect(engine)
    if "condominiums" not in inspector.get_table_names():
        print("⚠️  Tabla condominiums no existe aún; se creará al iniciar la app.")
        return False

    columns = [col["name"] for col in inspector.get_columns("condominiums")]
    if "settings" in columns:
        print("✅ Columna settings ya existe en condominiums")
        return True

    print("📝 Agregando columna settings a condominiums...")
    with engine.begin() as conn:
        if USE_SQLITE:
            conn.execute(text("ALTER TABLE condominiums ADD COLUMN settings TEXT"))
        else:
            conn.execute(
                text(
                    "ALTER TABLE condominiums ADD COLUMN IF NOT EXISTS settings TEXT"
                )
            )
    print("✅ Columna settings agregada")
    return True


def backfill_default_settings() -> None:
    db = SessionLocal()
    try:
        condos = db.query(Condominium).all()
        updated = 0
        for condo in condos:
            if not condo.settings:
                apply_default_settings(condo)
                updated += 1
        if updated:
            db.commit()
            print(f"✅ Configuración por defecto aplicada a {updated} condominio(s)")
        else:
            print("✅ Todos los condominios ya tenían configuración")
    finally:
        db.close()


def main() -> None:
    print("🔧 Migración: condominium settings")
    ensure_settings_column()
    backfill_default_settings()
    print("✅ Migración completada")


if __name__ == "__main__":
  main()
