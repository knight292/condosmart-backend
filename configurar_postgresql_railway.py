#!/usr/bin/env python3
"""
Script para configurar PostgreSQL en Railway automáticamente
"""
import subprocess
import sys
import os

def run_command(cmd, description):
    """Ejecuta un comando y muestra el resultado"""
    print(f"\n📋 {description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=False
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr and result.returncode != 0:
            print(f"⚠️  {result.stderr}")
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, "", str(e)

def main():
    print("🔧 Configurando PostgreSQL en Railway")
    print("=" * 50)
    
    # Verificar Railway CLI
    print("\n📋 Paso 1: Verificando Railway CLI...")
    success, _, _ = run_command("railway --version", "Verificando Railway CLI")
    if not success:
        print("❌ Railway CLI no está instalado")
        print("Instala con: npm i -g @railway/cli")
        return
    
    # Verificar proyecto
    print("\n📋 Paso 2: Verificando proyecto actual...")
    run_command("cd backend && railway status", "Verificando proyecto")
    
    # Verificar si ya existe DATABASE_URL
    print("\n📋 Paso 3: Verificando DATABASE_URL actual...")
    success, output, _ = run_command(
        "cd backend && railway variables",
        "Verificando variables de entorno"
    )
    
    if "DATABASE_URL" in output:
        if "sqlite" in output.lower():
            print("⚠️  SQLite detectado. Necesitas cambiar a PostgreSQL.")
        elif "postgresql" in output.lower():
            print("✅ PostgreSQL ya está configurado!")
            return
    
    print("\n" + "=" * 50)
    print("📝 INSTRUCCIONES MANUALES:")
    print("=" * 50)
    print("""
Como Railway CLI requiere interacción, sigue estos pasos:

1. Ve a: https://railway.app
2. Inicia sesión y selecciona tu proyecto "striking-intuition"
3. Haz clic en "+ New" (botón verde arriba)
4. Selecciona "Database" → "Add PostgreSQL"
5. Railway creará automáticamente PostgreSQL
6. Haz clic en el nuevo servicio "Postgres"
7. Ve a "Variables" y copia el valor de DATABASE_URL
8. Vuelve a tu servicio backend
9. Ve a "Variables" → Edita o crea DATABASE_URL
10. Pega el valor de PostgreSQL que copiaste
11. Guarda los cambios

O ejecuta estos comandos en tu terminal (requiere interacción):

  cd backend
  railway add
  # Selecciona "Database" cuando te pregunte
  # Selecciona "PostgreSQL"
  
  # Luego copia el DATABASE_URL del servicio PostgreSQL:
  railway variables --service postgres
  
  # Y configúralo en tu servicio backend:
  railway variables set DATABASE_URL="<valor-copiado>"
""")
    
    print("\n✅ Script completado. Sigue las instrucciones arriba.")

if __name__ == "__main__":
    main()
