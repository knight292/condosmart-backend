#!/usr/bin/env python3
"""
Script para verificar que PaymentMethod se importe correctamente
Ejecuta esto antes de iniciar el backend para verificar que no hay errores
"""

import sys
import os

# Agregar el directorio backend al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("🔍 Verificando importaciones...\n")
    
    print("1️⃣ Importando Base...")
    from app.db import Base, engine
    print("   ✅ Base importado")
    
    print("\n2️⃣ Importando modelos...")
    from app.models import PaymentMethod, Condominium, User
    print("   ✅ PaymentMethod importado")
    print("   ✅ Condominium importado")
    print("   ✅ User importado")
    
    print("\n3️⃣ Verificando que PaymentMethod esté en Base.metadata...")
    if 'payment_methods' in Base.metadata.tables:
        print("   ✅ Tabla 'payment_methods' registrada en metadata")
        table = Base.metadata.tables['payment_methods']
        print(f"   📋 Columnas: {len(table.columns)}")
        for col in table.columns:
            print(f"      - {col.name} ({col.type})")
    else:
        print("   ⚠️  Tabla 'payment_methods' NO está en metadata")
        print("   📋 Tablas registradas:")
        for table_name in Base.metadata.tables.keys():
            print(f"      - {table_name}")
    
    print("\n4️⃣ Intentando crear todas las tablas...")
    Base.metadata.create_all(bind=engine)
    print("   ✅ Tablas creadas/verificadas")
    
    print("\n✅ Todas las verificaciones pasaron!")
    print("\n💡 Ahora puedes iniciar el backend con:")
    print("   python -m uvicorn app.main:app --reload")
    
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    print("\n💡 Verifica que:")
    print("   - Estés en el directorio backend")
    print("   - Todos los archivos estén presentes")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

