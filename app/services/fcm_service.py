import requests
import os
from typing import Optional, Dict, Any

class FCMService:
    def __init__(self):
        self.server_key = os.getenv("FCM_SERVER_KEY", "")
        self.api_url = "https://fcm.googleapis.com/fcm/send"
        self.enabled = os.getenv("FCM_ENABLED", "false").lower() == "true" and bool(self.server_key)
    
    def send_notification(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Envía una notificación push a un dispositivo"""
        if not self.enabled:
            print(f"📱 FCM deshabilitado. Se enviaría a {device_token}: {title}")
            return True
        
        if not device_token:
            print("⚠️ Token de dispositivo no proporcionado")
            return False
        
        try:
            headers = {
                "Authorization": f"key={self.server_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "to": device_token,
                "notification": {
                    "title": title,
                    "body": body,
                    "sound": "default"
                },
                "data": data or {}
            }
            
            response = requests.post(self.api_url, json=payload, headers=headers)
            
            if response.status_code == 200:
                print(f"✅ Notificación push enviada a {device_token}: {title}")
                return True
            else:
                print(f"❌ Error enviando notificación push: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error enviando notificación push: {e}")
            return False
    
    def send_shift_assigned_notification(
        self,
        device_token: str,
        guard_name: str,
        shift_date: str,
        shift_type: str
    ) -> bool:
        """Envía notificación cuando se asigna un turno"""
        shift_type_label = {
            "morning": "Mañana",
            "afternoon": "Tarde",
            "night": "Noche",
            "full_day": "Día Completo"
        }.get(shift_type, shift_type)
        
        title = "Nuevo Turno Asignado"
        body = f"Tienes un turno el {shift_date} - {shift_type_label}"
        
        data = {
            "type": "shift_assigned",
            "shift_date": shift_date,
            "shift_type": shift_type
        }
        
        return self.send_notification(device_token, title, body, data)
    
    def send_shift_reminder_notification(
        self,
        device_token: str,
        shift_date: str,
        shift_type: str
    ) -> bool:
        """Envía notificación de recordatorio antes del turno"""
        shift_type_label = {
            "morning": "Mañana",
            "afternoon": "Tarde",
            "night": "Noche",
            "full_day": "Día Completo"
        }.get(shift_type, shift_type)
        
        title = "Recordatorio de Turno"
        body = f"Tu turno es mañana: {shift_date} - {shift_type_label}"
        
        data = {
            "type": "shift_reminder",
            "shift_date": shift_date,
            "shift_type": shift_type
        }
        
        return self.send_notification(device_token, title, body, data)

