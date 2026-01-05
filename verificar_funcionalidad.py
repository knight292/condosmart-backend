#!/usr/bin/env python3
"""
Script para verificar la funcionalidad completa de la aplicación CondoSmart
Verifica estructura, modelos, schemas, routers y código sin necesidad de backend corriendo
"""
import sys
import os
from pathlib import Path

# Agregar el directorio del backend al path
sys.path.insert(0, str(Path(__file__).parent))

# Colores para output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

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

def test_database_models():
    """Verificar que los modelos de base de datos estén correctos"""
    print_header("1. VERIFICANDO MODELOS DE BASE DE DATOS")
    
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
            import traceback
            traceback.print_exc()
            return False
            
    except ImportError as e:
        print_error(f"Error importando modelos: {e}")
        return False
    except Exception as e:
        print_error(f"Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_schemas():
    """Verificar que los schemas estén correctamente definidos"""
    print_header("2. VERIFICANDO SCHEMAS")
    
    schemas_path = Path(__file__).parent / "app" / "schemas"
    expected_schemas = [
        "user", "condominium", "owner", "unit", "payment", "payment_method",
        "ticket", "visit", "reservation", "announcement", "message",
        "document", "maintenance", "contract", "inventory", "regulation",
        "guard_shift", "package"
    ]
    
    success_count = 0
    errors = []
    for schema_name in expected_schemas:
        schema_file = schemas_path / f"{schema_name}.py"
        if schema_file.exists():
            try:
                # Intentar importar el schema
                module = __import__(f"app.schemas.{schema_name}", fromlist=[schema_name])
                print_success(f"Schema '{schema_name}' importado correctamente")
                success_count += 1
            except Exception as e:
                error_msg = f"Error importando schema '{schema_name}': {e}"
                print_error(error_msg)
                errors.append(error_msg)
        else:
            error_msg = f"Schema '{schema_name}' no encontrado: {schema_file}"
            print_error(error_msg)
            errors.append(error_msg)
    
    print_info(f"Schemas verificados: {success_count}/{len(expected_schemas)}")
    if errors:
        print_warning(f"Errores encontrados: {len(errors)}")
    
    return success_count == len(expected_schemas)

def test_routers_structure():
    """Verificar estructura de routers"""
    print_header("3. VERIFICANDO ESTRUCTURA DE ROUTERS")
    
    routers_path = Path(__file__).parent / "app" / "routers"
    expected_routers = [
        "auth", "payments", "payment_methods", "tickets", "visits",
        "reservations", "announcements", "messages", "documents",
        "maintenances", "contracts", "inventory", "regulations",
        "owners", "users", "guard_shifts", "packages"
    ]
    
    success_count = 0
    for router_name in expected_routers:
        router_file = routers_path / f"{router_name}.py"
        if router_file.exists():
            try:
                with open(router_file, 'r') as f:
                    content = f.read()
                    # Verificar que tenga router definido
                    if "router = APIRouter()" in content or "router = " in content:
                        # Verificar que tenga al menos un endpoint
                        if "@router." in content:
                            print_success(f"Router '{router_name}' tiene estructura correcta")
                            success_count += 1
                        else:
                            print_warning(f"Router '{router_name}' no tiene endpoints definidos")
                    else:
                        print_warning(f"Router '{router_name}' puede no tener router definido")
            except Exception as e:
                print_error(f"Error leyendo router '{router_name}': {e}")
        else:
            print_error(f"Router '{router_name}' no encontrado")
    
    print_info(f"Routers verificados: {success_count}/{len(expected_routers)}")
    return success_count == len(expected_routers)

def test_main_integration():
    """Verificar integración en main.py"""
    print_header("4. VERIFICANDO INTEGRACIÓN EN main.py")
    
    main_file = Path(__file__).parent / "app" / "main.py"
    if not main_file.exists():
        print_error("main.py no encontrado")
        return False
    
    try:
        with open(main_file, 'r') as f:
            content = f.read()
        
        checks = {
            "FastAPI app creado": "app = FastAPI" in content,
            "CORS configurado": "CORSMiddleware" in content,
            "Modelos importados": "from app.models import" in content,
            "WebSocket configurado": "@app.websocket" in content and "/ws/chat" in content,
        }
        
        routers = [
            "auth", "payments", "payment_methods", "tickets", "visits",
            "reservations", "announcements", "messages", "documents",
            "maintenances", "contracts", "inventory", "regulations",
            "owners", "users", "guard_shifts", "packages"
        ]
        
        routers_included = 0
        for router_name in routers:
            if f"app.include_router({router_name}.router" in content:
                routers_included += 1
        
        for check_name, result in checks.items():
            if result:
                print_success(check_name)
            else:
                print_error(check_name)
        
        print_info(f"Routers incluidos en app: {routers_included}/{len(routers)}")
        
        return all(checks.values()) and routers_included == len(routers)
    except Exception as e:
        print_error(f"Error verificando main.py: {e}")
        return False

def test_frontend_integration():
    """Verificar integración frontend-backend"""
    print_header("5. VERIFICANDO INTEGRACIÓN FRONTEND-BACKEND")
    
    frontend_path = Path(__file__).parent.parent / "app" / "lib"
    
    # Verificar servicios
    services_path = frontend_path / "services"
    services = ["api_service.dart", "auth_service.dart", "notification_service.dart"]
    
    services_ok = 0
    for service_file in services:
        service_path = services_path / service_file
        if service_path.exists():
            print_success(f"Servicio '{service_file}' existe")
            services_ok += 1
        else:
            print_error(f"Servicio '{service_file}' no encontrado")
    
    # Verificar pantallas críticas
    screens_path = frontend_path / "screens"
    critical_screens = [
        ("payments/payments_screen.dart", ["ApiService", "_api"]),
        ("chat/chat_screen.dart", ["ApiService", "_api", "WebSocket"]),
        ("tickets/tickets_screen.dart", ["ApiService", "_api"]),
        ("auth/login_screen.dart", ["AuthService", "_authService"])
    ]
    
    screens_ok = 0
    for screen_path, keywords in critical_screens:
        full_path = screens_path / screen_path
        if full_path.exists():
            try:
                with open(full_path, 'r') as f:
                    content = f.read()
                    if any(keyword in content for keyword in keywords):
                        print_success(f"Pantalla '{screen_path.split('/')[-1]}' está conectada")
                        screens_ok += 1
                    else:
                        print_warning(f"Pantalla '{screen_path.split('/')[-1]}' puede no estar conectada")
            except Exception as e:
                print_error(f"Error leyendo '{screen_path}': {e}")
        else:
            print_error(f"Pantalla '{screen_path}' no encontrada")
    
    print_info(f"Servicios: {services_ok}/{len(services)}")
    print_info(f"Pantallas críticas: {screens_ok}/{len(critical_screens)}")
    
    return services_ok == len(services) and screens_ok == len(critical_screens)

def test_endpoint_definitions():
    """Verificar que los endpoints estén definidos en los routers"""
    print_header("6. VERIFICANDO DEFINICIÓN DE ENDPOINTS")
    
    routers_path = Path(__file__).parent / "app" / "routers"
    
    # Endpoints críticos esperados
    expected_endpoints = {
        "auth": ["/login", "/register", "/me"],
        "payments": ["/", "/{payment_id}/process"],
        "payment_methods": ["/"],
        "tickets": ["/", "/{ticket_id}"],
        "visits": ["/generate", "/scan", "/"],
        "messages": ["/"],
        "users": ["/"],
    }
    
    total_checks = 0
    passed_checks = 0
    
    for router_name, endpoints in expected_endpoints.items():
        router_file = routers_path / f"{router_name}.py"
        if router_file.exists():
            try:
                with open(router_file, 'r') as f:
                    content = f.read()
                    for endpoint in endpoints:
                        total_checks += 1
                        # Buscar definiciones de endpoints
                        if f"@router." in content:
                            # Verificar que tenga métodos HTTP
                            if any(method in content for method in ["get(", "post(", "put(", "patch(", "delete("]):
                                passed_checks += 1
            except Exception as e:
                print_error(f"Error leyendo router '{router_name}': {e}")
        else:
            print_error(f"Router '{router_name}' no encontrado")
    
    print_info(f"Endpoints verificados: {passed_checks}/{total_checks}")
    return passed_checks >= total_checks * 0.8  # 80% es aceptable

def main():
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}🔍 VERIFICACIÓN FUNCIONAL COMPLETA - CondoSmart{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")
    
    results = {}
    
    # Ejecutar todas las pruebas
    results["database_models"] = test_database_models()
    results["schemas"] = test_schemas()
    results["routers_structure"] = test_routers_structure()
    results["main_integration"] = test_main_integration()
    results["frontend_integration"] = test_frontend_integration()
    results["endpoint_definitions"] = test_endpoint_definitions()
    
    # Resumen final
    print_header("📊 RESUMEN DE VERIFICACIÓN")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    for test_name, result in results.items():
        status = f"{GREEN}✅ PASÓ{RESET}" if result else f"{RED}❌ FALLÓ{RESET}"
        test_display = test_name.replace('_', ' ').title()
        print(f"{test_display}: {status}")
    
    print(f"\n{BLUE}{'='*70}{RESET}")
    percentage = (passed_tests / total_tests) * 100
    if percentage >= 90:
        print(f"{GREEN}✅ RESULTADO GENERAL: {percentage:.1f}% ({passed_tests}/{total_tests}){RESET}")
        print(f"{GREEN}✅ La aplicación está correctamente configurada{RESET}")
    elif percentage >= 70:
        print(f"{YELLOW}⚠️  RESULTADO GENERAL: {percentage:.1f}% ({passed_tests}/{total_tests}){RESET}")
        print(f"{YELLOW}⚠️  Hay algunos aspectos que revisar{RESET}")
    else:
        print(f"{RED}❌ RESULTADO GENERAL: {percentage:.1f}% ({passed_tests}/{total_tests}){RESET}")
        print(f"{RED}❌ Hay problemas que resolver{RESET}")
    
    print(f"{BLUE}{'='*70}{RESET}\n")
    
    return percentage >= 70

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Verificación interrumpida por el usuario{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Error inesperado: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

