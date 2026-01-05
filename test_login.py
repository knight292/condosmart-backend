#!/usr/bin/env python3
"""
Script para probar el login directamente
"""
import requests
import sys

BASE_URL = "http://localhost:8000/api"

def test_login():
    email = "juan.perez@test.com"
    password = "test123"
    
    print(f"🔍 Probando login con:")
    print(f"   Email: {email}")
    print(f"   Password: {password}\n")
    
    try:
        # Probar login
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": email,  # OAuth2 usa 'username'
                "password": password,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📊 Response: {response.text[:200]}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Login exitoso!")
            print(f"   Token recibido: {data.get('access_token', '')[:50]}...")
            
            # Probar obtener info del usuario
            token = data.get('access_token')
            headers = {"Authorization": f"Bearer {token}"}
            
            response2 = requests.get(f"{BASE_URL}/auth/me", headers=headers)
            if response2.status_code == 200:
                user = response2.json()
                print(f"\n✅ Usuario obtenido:")
                print(f"   Nombre: {user.get('full_name')}")
                print(f"   Email: {user.get('email')}")
                print(f"   Role: {user.get('role')}")
                print(f"   Condominio: {user.get('condominium_id')}")
            else:
                print(f"\n⚠️  Error al obtener usuario: {response2.status_code}")
                print(f"   {response2.text}")
        else:
            print(f"\n❌ Login falló")
            print(f"   Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se pudo conectar al backend")
        print("   Asegúrate de que el backend esté corriendo en http://localhost:8000")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_login()

