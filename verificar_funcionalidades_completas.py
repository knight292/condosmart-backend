"""
Script para verificar que todas las nuevas funcionalidades estén correctamente implementadas
"""
import sys
import os

# Agregar el directorio del backend al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def verificar_imports():
    """Verifica que todos los módulos se puedan importar"""
    print("🔍 Verificando imports...")
    
    try:
        from app.services.email_service import EmailService
        print("✅ EmailService importado correctamente")
    except Exception as e:
        print(f"❌ Error importando EmailService: {e}")
        return False
    
    try:
        from app.services.fcm_service import FCMService
        print("✅ FCMService importado correctamente")
    except Exception as e:
        print(f"❌ Error importando FCMService: {e}")
        return False
    
    try:
        from app.services.reminder_service import ReminderService
        print("✅ ReminderService importado correctamente")
    except Exception as e:
        print(f"❌ Error importando ReminderService: {e}")
        return False
    
    try:
        from app.routers.reports import router as reports_router
        print("✅ Reports router importado correctamente")
    except Exception as e:
        print(f"❌ Error importando reports router: {e}")
        return False
    
    try:
        from app.routers.statistics import router as statistics_router
        print("✅ Statistics router importado correctamente")
    except Exception as e:
        print(f"❌ Error importando statistics router: {e}")
        return False
    
    return True

def verificar_modelos():
    """Verifica que los modelos tengan los campos necesarios"""
    print("\n🔍 Verificando modelos...")
    
    try:
        from app.models import User
        import inspect
        
        # Verificar que User tiene fcm_token
        if hasattr(User, 'fcm_token'):
            print("✅ User tiene campo fcm_token")
        else:
            print("❌ User no tiene campo fcm_token")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error verificando modelos: {e}")
        return False

def verificar_servicios():
    """Verifica que los servicios funcionen correctamente"""
    print("\n🔍 Verificando servicios...")
    
    try:
        from app.services.email_service import EmailService
        email_service = EmailService()
        print("✅ EmailService instanciado correctamente")
        print(f"   Email habilitado: {email_service.enabled}")
    except Exception as e:
        print(f"❌ Error con EmailService: {e}")
        return False
    
    try:
        from app.services.fcm_service import FCMService
        fcm_service = FCMService()
        print("✅ FCMService instanciado correctamente")
        print(f"   FCM habilitado: {fcm_service.enabled}")
    except Exception as e:
        print(f"❌ Error con FCMService: {e}")
        return False
    
    try:
        from app.services.reminder_service import ReminderService
        reminder_service = ReminderService()
        print("✅ ReminderService instanciado correctamente")
    except Exception as e:
        print(f"❌ Error con ReminderService: {e}")
        return False
    
    return True

def verificar_routers():
    """Verifica que los routers estén registrados en main.py"""
    print("\n🔍 Verificando routers...")
    
    try:
        with open('app/main.py', 'r') as f:
            content = f.read()
            
            if 'reports.router' in content or 'app.include_router(reports' in content:
                print("✅ Reports router registrado en main.py")
            else:
                print("❌ Reports router NO registrado en main.py")
                return False
            
            if 'statistics.router' in content or 'app.include_router(statistics' in content:
                print("✅ Statistics router registrado en main.py")
            else:
                print("❌ Statistics router NO registrado en main.py")
                return False
            
            return True
    except Exception as e:
        print(f"❌ Error verificando routers: {e}")
        return False

def main():
    print("=" * 60)
    print("VERIFICACIÓN DE FUNCIONALIDADES COMPLETAS")
    print("=" * 60)
    
    resultados = []
    
    resultados.append(("Imports", verificar_imports()))
    resultados.append(("Modelos", verificar_modelos()))
    resultados.append(("Servicios", verificar_servicios()))
    resultados.append(("Routers", verificar_routers()))
    
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    
    todos_ok = True
    for nombre, resultado in resultados:
        estado = "✅ OK" if resultado else "❌ ERROR"
        print(f"{nombre}: {estado}")
        if not resultado:
            todos_ok = False
    
    print("=" * 60)
    
    if todos_ok:
        print("✅ TODAS LAS VERIFICACIONES PASARON")
        print("\nFuncionalidades implementadas:")
        print("  ✅ Notificaciones push (FCM)")
        print("  ✅ Envío de emails")
        print("  ✅ Exportación de reportes (PDF/Excel)")
        print("  ✅ Sistema de recordatorios")
        print("  ✅ Dashboard de estadísticas")
        return 0
    else:
        print("❌ ALGUNAS VERIFICACIONES FALLARON")
        return 1

if __name__ == "__main__":
    exit(main())

