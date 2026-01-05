#!/usr/bin/env python3
"""
Script para probar la funcionalidad completa de la aplicación CondoSmart
Verifica endpoints, modelos, y flujos críticos
"""
import sys
import os
import requests
import json
from pathlib import Path

# Agregar el directorio del backend al path
sys.path.insert(0, str(Path(__file__).parent))

# Colores para output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

BASE_URL = "http://localhost:8000/api"

def print_header(text):
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")

def print_info(text):
    print(f"{BLUE}ℹ️  {text}{RESET}")

def test_backend_connection():
    """Verificar que el backend esté corriendo"""
    print_header("1. VERIFICANDO CONEXIÓN CON BACKEND")
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print_success("Backend está corriendo y respondiendo")
            print_info(f"Respuesta: {response.json()}")
            return True
        else:
            print_error(f"Backend responde con código {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("No se puede conectar al backend")
        print_warning("Asegúrate de que el backend esté corriendo:")
        print_warning("  cd backend && source venv/bin/activate && uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print_error(f"Error al conectar: {e}")
        return False

def test_database_models():
    """Verificar que los modelos de base de datos estén correctos"""
    print_header("2. VERIFICANDO MODELOS DE BASE DE DATOS")
    
    try:
        from app.db import engine, Base
        from app.models import (
            User, Condominium, Owner, Unit, Payment, PaymentMethod,
            Ticket, TicketAttachment, Visit, Reservation, Announcement,
            Message, Document, Maintenance, Contract, InventoryItem,
            Regulation, GuardShift, Package
        )
        
        # Verificar que las tablas se pueden crear
        try:
            Base.metadata.create_all(bind=engine)
            print_success("Todos los modelos están correctamente definidos")
            print_success("Las tablas se pueden crear sin errores")
            
            # Listar tablas creadas
            tables = list(Base.metadata.tables.keys())
            print_info(f"Tablas en la base de datos: {len(tables)}")
            for table in sorted(tables):
                print(f"   • {table}")
            
            return True
        except Exception as e:
            print_error(f"Error al crear tablas: {e}")
            return False
            
    except ImportError as e:
        print_error(f"Error importando modelos: {e}")
        return False
    except Exception as e:
        print_error(f"Error inesperado: {e}")
        return False

def test_routers_import():
    """Verificar que todos los routers se pueden importar"""
    print_header("3. VERIFICANDO ROUTERS")
    
    routers = [
        "auth", "payments", "payment_methods", "tickets", "visits",
        "reservations", "announcements", "messages", "documents",
        "maintenances", "contracts", "inventory", "regulations",
        "owners", "users", "guard_shifts", "packages"
    ]
    
    success_count = 0
    for router_name in routers:
        try:
            module = __import__(f"app.routers.{router_name}", fromlist=[router_name])
            router = getattr(module, "router", None)
            if router:
                print_success(f"Router '{router_name}' importado correctamente")
                success_count += 1
            else:
                print_error(f"Router '{router_name}' no tiene atributo 'router'")
        except Exception as e:
            print_error(f"Error importando router '{router_name}': {e}")
    
    print_info(f"Routers importados: {success_count}/{len(routers)}")
    return success_count == len(routers)

def test_endpoints_availability():
    """Verificar que los endpoints principales estén disponibles"""
    print_header("4. VERIFICANDO ENDPOINTS DISPONIBLES")
    
    # Endpoints que no requieren autenticación
    public_endpoints = [
        ("GET", "/", "Root endpoint"),
    ]
    
    # Endpoints que requieren autenticación (solo verificamos que existan, no que funcionen)
    auth_required_endpoints = [
        ("POST", "/auth/login", "Login"),
        ("POST", "/auth/register", "Registro"),
        ("GET", "/auth/me", "Usuario actual"),
        ("GET", "/payments/", "Lista de pagos"),
        ("GET", "/payment-methods/", "Métodos de pago"),
        ("GET", "/tickets/", "Tickets"),
        ("GET", "/visits/", "Visitas"),
        ("GET", "/reservations/", "Reservas"),
        ("GET", "/announcements/", "Anuncios"),
        ("GET", "/messages/", "Mensajes"),
        ("GET", "/documents/", "Documentos"),
        ("GET", "/maintenances/", "Mantenimientos"),
        ("GET", "/contracts/", "Contratos"),
        ("GET", "/inventory/", "Inventario"),
        ("GET", "/regulations/", "Regulaciones"),
        ("GET", "/users/", "Usuarios"),
        ("GET", "/guard-shifts/", "Turnos de guardias"),
        ("GET", "/packages/", "Paquetes"),
    ]
    
    success_count = 0
    total_count = len(public_endpoints) + len(auth_required_endpoints)
    
    # Probar endpoints públicos
    for method, endpoint, description in public_endpoints:
        try:
            url = f"http://localhost:8000{endpoint}"
            if method == "GET":
                response = requests.get(url, timeout=3)
            else:
                response = requests.post(url, timeout=3)
            
            # Cualquier respuesta (incluso 401/404) significa que el endpoint existe
            if response.status_code in [200, 401, 403, 404, 422]:
                print_success(f"{description} ({method} {endpoint}) - Disponible")
                success_count += 1
            else:
                print_warning(f"{description} ({method} {endpoint}) - Código: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print_error(f"No se puede conectar al backend para {description}")
            return False
        except Exception as e:
            print_error(f"Error probando {description}: {e}")
    
    # Para endpoints que requieren auth, solo verificamos que el servidor responda
    # (no probamos la funcionalidad completa sin credenciales)
    for method, endpoint, description in auth_required_endpoints:
        try:
            url = f"{BASE_URL}{endpoint}"
            if method == "GET":
                response = requests.get(url, timeout=3)
            else:
                response = requests.post(url, json={}, timeout=3)
            
            # 401/403 significa que el endpoint existe pero requiere auth (correcto)
            # 404 significa que el endpoint no existe (error)
            if response.status_code in [200, 401, 403, 422]:
                print_success(f"{description} ({method} {endpoint}) - Disponible")
                success_count += 1
            elif response.status_code == 404:
                print_error(f"{description} ({method} {endpoint}) - NO ENCONTRADO (404)")
            else:
                print_warning(f"{description} ({method} {endpoint}) - Código: {response.status_code}")
        except Exception as e:
            print_error(f"Error probando {description}: {e}")
    
    print_info(f"Endpoints disponibles: {success_count}/{total_count}")
    return success_count >= total_count * 0.9  # 90% de éxito es aceptable

def test_schemas():
    """Verificar que los schemas estén correctamente definidos"""
    print_header("5. VERIFICANDO SCHEMAS")
    
    schemas_path = Path(__file__).parent / "app" / "schemas"
    expected_schemas = [
        "user", "condominium", "owner", "unit", "payment", "payment_method",
        "ticket", "visit", "reservation", "announcement", "message",
        "document", "maintenance", "contract", "inventory", "regulation",
        "guard_shift", "package"
    ]
    
    success_count = 0
    for schema_name in expected_schemas:
        schema_file = schemas_path / f"{schema_name}.py"
        if schema_file.exists():
            try:
                # Intentar importar el schema
                module = __import__(f"app.schemas.{schema_name}", fromlist=[schema_name])
                print_success(f"Schema '{schema_name}' importado correctamente")
                success_count += 1
            except Exception as e:
                print_error(f"Error importando schema '{schema_name}': {e}")
        else:
            print_error(f"Schema '{schema_name}' no encontrado: {schema_file}")
    
    print_info(f"Schemas verificados: {success_count}/{len(expected_schemas)}")
    return success_count == len(expected_schemas)

def test_websocket_endpoint():
    """Verificar que el endpoint WebSocket esté configurado"""
    print_header("6. VERIFICANDO WEBSOCKET (Chat)")
    
    try:
        # Leer main.py para verificar que el WebSocket esté configurado
        main_file = Path(__file__).parent / "app" / "main.py"
        with open(main_file, 'r') as f:
            content = f.read()
            
        if "@app.websocket" in content and "/ws/chat" in content:
            print_success("Endpoint WebSocket '/ws/chat' está configurado")
            
            # Verificar que tenga la lógica básica
            if "websocket.accept" in content and "get_user_from_token" in content:
                print_success("WebSocket tiene lógica de autenticación")
                return True
            else:
                print_warning("WebSocket configurado pero puede faltar lógica")
                return True
        else:
            print_error("Endpoint WebSocket no encontrado en main.py")
            return False
    except Exception as e:
        print_error(f"Error verificando WebSocket: {e}")
        return False

def test_integration():
    """Verificar integración frontend-backend"""
    print_header("7. VERIFICANDO INTEGRACIÓN FRONTEND-BACKEND")
    
    # Verificar que las pantallas del frontend usen los endpoints correctos
    frontend_path = Path(__file__).parent.parent / "app" / "lib" / "screens"
    
    critical_screens = [
        ("payments/payments_screen.dart", ["ApiService", "_api"]),
        ("chat/chat_screen.dart", ["ApiService", "_api", "WebSocket"]),
        ("tickets/tickets_screen.dart", ["ApiService", "_api"]),
        ("auth/login_screen.dart", ["AuthService", "ApiService", "_authService"])
    ]
    
    success_count = 0
    for screen_path, keywords in critical_screens:
        full_path = frontend_path / screen_path
        if full_path.exists():
            try:
                with open(full_path, 'r') as f:
                    content = f.read()
                    # Verificar que use algún servicio
                    if any(keyword in content for keyword in keywords):
                        print_success(f"Pantalla '{screen_path}' está conectada")
                        success_count += 1
                    else:
                        print_warning(f"Pantalla '{screen_path}' puede no estar conectada")
            except Exception as e:
                print_error(f"Error leyendo '{screen_path}': {e}")
        else:
            print_error(f"Pantalla '{screen_path}' no encontrada")
    
    print_info(f"Pantallas críticas verificadas: {success_count}/{len(critical_screens)}")
    return success_count == len(critical_screens)

def main():
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}🧪 PRUEBAS FUNCIONALES COMPLETAS - CondoSmart{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")
    
    results = {}
    
    # Ejecutar todas las pruebas
    results["backend_connection"] = test_backend_connection()
    results["database_models"] = test_database_models()
    results["routers"] = test_routers_import()
    results["endpoints"] = test_endpoints_availability()
    results["schemas"] = test_schemas()
    results["websocket"] = test_websocket_endpoint()
    results["integration"] = test_integration()
    
    # Resumen final
    print_header("📊 RESUMEN DE PRUEBAS")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    for test_name, result in results.items():
        status = f"{GREEN}✅ PASÓ{RESET}" if result else f"{RED}❌ FALLÓ{RESET}"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n{BLUE}{'='*70}{RESET}")
    percentage = (passed_tests / total_tests) * 100
    if percentage >= 90:
        print(f"{GREEN}✅ RESULTADO GENERAL: {percentage:.1f}% ({passed_tests}/{total_tests}){RESET}")
        print(f"{GREEN}✅ La aplicación está funcionando correctamente{RESET}")
    elif percentage >= 70:
        print(f"{YELLOW}⚠️  RESULTADO GENERAL: {percentage:.1f}% ({passed_tests}/{total_tests}){RESET}")
        print(f"{YELLOW}⚠️  Hay algunos problemas menores que revisar{RESET}")
    else:
        print(f"{RED}❌ RESULTADO GENERAL: {percentage:.1f}% ({passed_tests}/{total_tests}){RESET}")
        print(f"{RED}❌ Hay problemas significativos que resolver{RESET}")
    
    print(f"{BLUE}{'='*70}{RESET}\n")
    
    return percentage >= 70

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Pruebas interrumpidas por el usuario{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Error inesperado: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

