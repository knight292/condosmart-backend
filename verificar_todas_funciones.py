#!/usr/bin/env python3
"""
Script para verificar que todas las funciones de la app estén configuradas correctamente
"""
import os
import sys
import importlib.util
from pathlib import Path

# Colores para output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check_file_exists(filepath, description):
    """Verifica si un archivo existe"""
    if os.path.exists(filepath):
        print(f"{GREEN}✅{RESET} {description}: {filepath}")
        return True
    else:
        print(f"{RED}❌{RESET} {description}: {filepath} - NO ENCONTRADO")
        return False

def check_import(module_path, module_name, description):
    """Verifica si un módulo se puede importar"""
    try:
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print(f"{GREEN}✅{RESET} {description}: {module_name}")
            return True
    except Exception as e:
        print(f"{RED}❌{RESET} {description}: {module_name} - ERROR: {e}")
        return False
    return False

def main():
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}🔍 VERIFICACIÓN COMPLETA DE FUNCIONALIDADES - CondoSmart{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")
    
    backend_path = Path(__file__).parent
    app_path = backend_path / "app"
    routers_path = app_path / "routers"
    models_path = app_path / "models"
    schemas_path = app_path / "schemas"
    
    results = {
        "routers": [],
        "models": [],
        "schemas": [],
        "main_integration": []
    }
    
    # 1. Verificar routers
    print(f"\n{BLUE}📋 1. VERIFICANDO ROUTERS (Backend){RESET}")
    print("-" * 70)
    
    expected_routers = [
        "auth", "payments", "payment_methods", "tickets", "visits",
        "reservations", "announcements", "messages", "documents",
        "maintenances", "contracts", "inventory", "regulations",
        "owners", "users", "guard_shifts", "packages"
    ]
    
    for router_name in expected_routers:
        router_file = routers_path / f"{router_name}.py"
        if check_file_exists(router_file, f"Router {router_name}"):
            results["routers"].append(router_name)
            # Verificar que tenga al menos un endpoint
            try:
                with open(router_file, 'r') as f:
                    content = f.read()
                    if "@router." in content:
                        print(f"   {GREEN}   ✓{RESET} Tiene endpoints definidos")
                    else:
                        print(f"   {YELLOW}   ⚠{RESET} No se encontraron endpoints")
            except Exception as e:
                print(f"   {RED}   ✗{RESET} Error leyendo archivo: {e}")
    
    # 2. Verificar modelos
    print(f"\n{BLUE}📦 2. VERIFICANDO MODELOS (Backend){RESET}")
    print("-" * 70)
    
    expected_models = [
        "user", "condominium", "owner", "unit", "payment", "payment_method",
        "ticket", "visit", "reservation", "announcement",
        "message", "document", "maintenance", "contract", "inventory",
        "regulation", "guard_shift", "package"
    ]
    
    # Modelos especiales que están dentro de otros archivos
    special_models = {
        "ticket_attachment": "ticket",  # TicketAttachment está en ticket.py
        "inventory_item": "inventory"    # InventoryItem está en inventory.py
    }
    
    for model_name in expected_models:
        model_file = models_path / f"{model_name}.py"
        if check_file_exists(model_file, f"Modelo {model_name}"):
            results["models"].append(model_name)
            # Verificar modelos especiales dentro del archivo
            if model_name in ["ticket", "inventory"]:
                try:
                    with open(model_file, 'r') as f:
                        content = f.read()
                        if model_name == "ticket" and "class TicketAttachment" in content:
                            print(f"   {GREEN}   ✓{RESET} TicketAttachment encontrado dentro de ticket.py")
                            results["models"].append("ticket_attachment")
                        elif model_name == "inventory" and "class InventoryItem" in content:
                            print(f"   {GREEN}   ✓{RESET} InventoryItem encontrado dentro de inventory.py")
                            results["models"].append("inventory_item")
                except:
                    pass
    
    # 3. Verificar schemas
    print(f"\n{BLUE}📝 3. VERIFICANDO SCHEMAS (Backend){RESET}")
    print("-" * 70)
    
    # Schemas especiales que están dentro de otros archivos
    schema_special_cases = {
        "ticket_attachment": "ticket",  # TicketAttachmentResponse está en ticket.py
        "inventory_item": "inventory"   # InventoryItem schemas están en inventory.py
    }
    
    for schema_name in expected_models:
        schema_file = schemas_path / f"{schema_name}.py"
        if check_file_exists(schema_file, f"Schema {schema_name}"):
            results["schemas"].append(schema_name)
            # Verificar schemas especiales dentro del archivo
            if schema_name in ["ticket", "inventory"]:
                try:
                    with open(schema_file, 'r') as f:
                        content = f.read()
                        if schema_name == "ticket" and "TicketAttachmentResponse" in content:
                            print(f"   {GREEN}   ✓{RESET} TicketAttachmentResponse encontrado dentro de ticket.py")
                            results["schemas"].append("ticket_attachment")
                        elif schema_name == "inventory" and "InventoryItem" in content:
                            print(f"   {GREEN}   ✓{RESET} InventoryItem schemas encontrados dentro de inventory.py")
                            results["schemas"].append("inventory_item")
                except:
                    pass
    
    # 4. Verificar integración en main.py
    print(f"\n{BLUE}🔗 4. VERIFICANDO INTEGRACIÓN EN main.py{RESET}")
    print("-" * 70)
    
    main_file = app_path / "main.py"
    if check_file_exists(main_file, "Archivo main.py"):
        try:
            with open(main_file, 'r') as f:
                main_content = f.read()
                
                # Verificar que los routers estén importados
                for router_name in expected_routers:
                    if f"import {router_name}" in main_content or f", {router_name}" in main_content:
                        print(f"   {GREEN}   ✓{RESET} Router '{router_name}' importado")
                        results["main_integration"].append(router_name)
                    else:
                        print(f"   {RED}   ✗{RESET} Router '{router_name}' NO importado")
                
                # Verificar que los routers estén incluidos
                for router_name in expected_routers:
                    if f"app.include_router({router_name}.router" in main_content:
                        print(f"   {GREEN}   ✓{RESET} Router '{router_name}' incluido en app")
                    else:
                        print(f"   {YELLOW}   ⚠{RESET} Router '{router_name}' puede no estar incluido")
                
                # Verificar modelos importados
                if "from app.models import" in main_content:
                    print(f"   {GREEN}   ✓{RESET} Modelos importados")
                else:
                    print(f"   {YELLOW}   ⚠{RESET} Modelos pueden no estar importados")
                    
        except Exception as e:
            print(f"   {RED}   ✗{RESET} Error leyendo main.py: {e}")
    
    # 5. Verificar frontend screens
    print(f"\n{BLUE}📱 5. VERIFICANDO PANTALLAS (Frontend){RESET}")
    print("-" * 70)
    
    frontend_path = backend_path.parent / "app" / "lib" / "screens"
    expected_screens = [
        ("auth/login_screen.dart", "Login"),
        ("payments/payments_screen.dart", "Pagos"),
        ("payments/payment_methods_config_screen.dart", "Configuración Métodos de Pago"),
        ("chat/chat_screen.dart", "Chat"),
        ("tickets/tickets_screen.dart", "Tickets"),
        ("tickets/create_ticket_screen.dart", "Crear Ticket"),
        ("visits/visits_screen.dart", "Visitas"),
        ("visits/create_visit_screen.dart", "Crear Visita"),
        ("reservations/reservations_screen.dart", "Reservas"),
        ("reservations/create_reservation_screen.dart", "Crear Reserva"),
        ("announcements/announcements_screen.dart", "Anuncios"),
        ("documents/documents_screen.dart", "Documentos"),
        ("documents/create_document_screen.dart", "Crear Documento"),
        ("maintenances/maintenances_screen.dart", "Mantenimientos"),
        ("maintenances/create_maintenance_screen.dart", "Crear Mantenimiento"),
        ("contracts/contracts_screen.dart", "Contratos"),
        ("contracts/create_contract_screen.dart", "Crear Contrato"),
        ("inventory/inventory_screen.dart", "Inventario"),
        ("inventory/create_inventory_item_screen.dart", "Crear Item Inventario"),
        ("regulations/regulations_screen.dart", "Regulaciones"),
        ("regulations/create_regulation_screen.dart", "Crear Regulación"),
        ("guards/guard_shifts_screen.dart", "Turnos Guardias"),
        ("guards/create_guard_shift_screen.dart", "Crear Turno Guardia"),
        ("guards/current_guard_screen.dart", "Guardia Actual"),
        ("packages/packages_screen.dart", "Paquetes"),
        ("packages/create_package_screen.dart", "Crear Paquete"),
        ("users/users_management_screen.dart", "Gestión Usuarios"),
        ("users/create_user_screen.dart", "Crear Usuario"),
        ("home/home_screen.dart", "Home"),
        ("home/admin_dashboard_screen.dart", "Dashboard Admin"),
        ("home/resident_dashboard_screen.dart", "Dashboard Residente"),
        ("home/guard_dashboard_screen.dart", "Dashboard Guardia"),
        ("profile/profile_screen.dart", "Perfil"),
        ("notifications/notifications_screen.dart", "Notificaciones"),
        ("reports/reports_screen.dart", "Reportes"),
    ]
    
    screens_found = 0
    for screen_path, screen_name in expected_screens:
        full_path = frontend_path / screen_path
        if check_file_exists(full_path, f"Pantalla {screen_name}"):
            screens_found += 1
    
    # 6. Verificar servicios frontend
    print(f"\n{BLUE}⚙️  6. VERIFICANDO SERVICIOS (Frontend){RESET}")
    print("-" * 70)
    
    services_path = backend_path.parent / "app" / "lib" / "services"
    expected_services = [
        ("api_service.dart", "API Service"),
        ("auth_service.dart", "Auth Service"),
        ("notification_service.dart", "Notification Service"),
        ("report_service.dart", "Report Service"),
    ]
    
    for service_file, service_name in expected_services:
        full_path = services_path / service_file
        check_file_exists(full_path, f"Servicio {service_name}")
    
    # 7. Resumen
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}📊 RESUMEN DE VERIFICACIÓN{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")
    
    total_routers = len(expected_routers)
    found_routers = len(results["routers"])
    print(f"Routers: {found_routers}/{total_routers} encontrados")
    
    total_models = len(expected_models)
    found_models = len(results["models"])
    print(f"Modelos: {found_models}/{total_models} encontrados")
    
    total_schemas = len(expected_models)
    found_schemas = len(results["schemas"])
    print(f"Schemas: {found_schemas}/{total_schemas} encontrados")
    
    total_screens = len(expected_screens)
    print(f"Pantallas: {screens_found}/{total_screens} encontradas")
    
    # Calcular porcentaje
    total_checks = total_routers + total_models + total_schemas + total_screens
    total_found = found_routers + found_models + found_schemas + screens_found
    percentage = (total_found / total_checks) * 100 if total_checks > 0 else 0
    
    print(f"\n{GREEN if percentage >= 90 else YELLOW if percentage >= 70 else RED}")
    print(f"✅ COMPLETITUD GENERAL: {percentage:.1f}%{RESET}\n")
    
    # Verificar problemas críticos
    print(f"{BLUE}🔍 VERIFICANDO PROBLEMAS CRÍTICOS{RESET}")
    print("-" * 70)
    
    critical_issues = []
    
    # Verificar que los routers críticos estén presentes
    critical_routers = ["auth", "payments", "users"]
    for router in critical_routers:
        if router not in results["routers"]:
            critical_issues.append(f"Router crítico '{router}' no encontrado")
    
    # Verificar que los modelos críticos estén presentes
    critical_models = ["user", "condominium", "payment"]
    for model in critical_models:
        if model not in results["models"]:
            critical_issues.append(f"Modelo crítico '{model}' no encontrado")
    
    if critical_issues:
        print(f"{RED}❌ PROBLEMAS CRÍTICOS ENCONTRADOS:{RESET}")
        for issue in critical_issues:
            print(f"   {RED}• {issue}{RESET}")
    else:
        print(f"{GREEN}✅ No se encontraron problemas críticos{RESET}")
    
    print(f"\n{BLUE}{'='*70}{RESET}\n")
    
    return len(critical_issues) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

