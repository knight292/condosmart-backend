from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Usar SQLite si no hay DATABASE_URL configurado (modo prueba)
# IMPORTANTE: En producción (Railway), siempre usar PostgreSQL con DATABASE_URL
# SQLite solo para desarrollo local - los datos se pierden en cada deploy si se usa SQLite en Railway
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./test_condosmart.db"
    print("⚠️  Usando SQLite para pruebas (test_condosmart.db)")
    print("⚠️  ADVERTENCIA: SQLite NO es persistente en Railway. Usa PostgreSQL en producción.")
else:
    # Verificar que en producción se use PostgreSQL
    if "sqlite" in DATABASE_URL.lower():
        print("⚠️  ADVERTENCIA CRÍTICA: SQLite detectado en DATABASE_URL de producción.")
        print("⚠️  Los datos se perderán en cada deploy. Usa PostgreSQL en Railway.")
    else:
        print(f"✅ Usando base de datos persistente: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'PostgreSQL'}")

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
