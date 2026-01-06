# Helper para manejar UUID compatible con SQLite y PostgreSQL
import os
import uuid
from sqlalchemy import String

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test_condosmart.db")
USE_SQLITE = "sqlite" in DATABASE_URL.lower()

if USE_SQLITE:
    # Para SQLite, usar String(36) para almacenar UUIDs como texto
    UUID = String(36)
    UUID_TYPE = String(36)
    
    def generate_uuid():
        """Genera un UUID como string para SQLite"""
        return str(uuid.uuid4())
else:
    # Para PostgreSQL, usar el tipo UUID nativo
    from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
    UUID = PostgresUUID(as_uuid=True)
    UUID_TYPE = PostgresUUID(as_uuid=True)
    
    def generate_uuid():
        """Genera un UUID como objeto UUID para PostgreSQL"""
        return uuid.uuid4()

# Exportar USE_SQLITE para uso en otros módulos
__all__ = ['UUID', 'UUID_TYPE', 'USE_SQLITE', 'DATABASE_URL', 'generate_uuid']
