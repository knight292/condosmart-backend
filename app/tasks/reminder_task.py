"""
Tarea programada para enviar recordatorios de turnos.
Ejecutar con: python -m app.tasks.reminder_task
O configurar como cron job: 0 8 * * * cd /path/to/backend && python -m app.tasks.reminder_task
"""
from app.services.reminder_service import ReminderService

if __name__ == "__main__":
    print("🔄 Ejecutando servicio de recordatorios...")
    service = ReminderService()
    service.check_and_send_reminders()
    print("✅ Servicio de recordatorios completado")

