from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.db import SessionLocal
from app.models import GuardShift, User
from app.services.email_service import EmailService
from app.services.fcm_service import FCMService
from app.routers.guard_shifts import _calculate_shift_times

class ReminderService:
    def __init__(self):
        self.email_service = EmailService()
        self.fcm_service = FCMService()
    
    def check_and_send_reminders(self):
        """Verifica turnos que empiezan en las próximas 24 horas y envía recordatorios"""
        db = SessionLocal()
        try:
            now = datetime.now()
            tomorrow = now + timedelta(days=1)
            
            # Buscar turnos programados que empiezan entre ahora y mañana
            shifts = db.query(GuardShift).filter(
                GuardShift.status == "scheduled",
                GuardShift.shift_date >= now,
                GuardShift.shift_date <= tomorrow
            ).all()
            
            reminders_sent = 0
            
            for shift in shifts:
                guard = db.query(User).filter(User.id == shift.guard_id).first()
                if not guard:
                    continue
                
                # Calcular tiempo hasta el turno
                time_until_shift = shift.shift_date - now
                hours_until = time_until_shift.total_seconds() / 3600
                
                # Enviar recordatorio si falta entre 12 y 24 horas
                if 12 <= hours_until <= 24:
                    shift_start, shift_end = _calculate_shift_times(shift.shift_date, shift.shift_type)
                    date_str = shift.shift_date.strftime("%d/%m/%Y %H:%M")
                    
                    # Enviar email
                    self.email_service.send_shift_reminder_email(
                        guard_email=guard.email,
                        guard_name=guard.full_name,
                        shift_date=shift.shift_date,
                        shift_type=shift.shift_type
                    )
                    
                    # Enviar notificación push
                    if guard.fcm_token:
                        self.fcm_service.send_shift_reminder_notification(
                            device_token=guard.fcm_token,
                            shift_date=date_str,
                            shift_type=shift.shift_type
                        )
                    
                    reminders_sent += 1
                    print(f"📧 Recordatorio enviado a {guard.full_name} para turno del {date_str}")
            
            print(f"✅ {reminders_sent} recordatorios enviados")
            return reminders_sent
        except Exception as e:
            print(f"❌ Error en servicio de recordatorios: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()

