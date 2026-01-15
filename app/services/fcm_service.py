import requests
import os
import json
from typing import Optional, Dict, Any
from google.oauth2 import service_account
from google.auth.transport.requests import Request

class FCMService:
    def __init__(self):
        self.server_key = os.getenv("FCM_SERVER_KEY", "")
        self.api_url = "https://fcm.googleapis.com/fcm/send"
        self.service_account_json = os.getenv("FCM_SERVICE_ACCOUNT_JSON", "")
        self.project_id = None
        self.credentials = None
        self.use_v1 = False
        if self.service_account_json:
            try:
                sa_info = json.loads(self.service_account_json)
                self.project_id = sa_info.get("project_id")
                self.credentials = service_account.Credentials.from_service_account_info(
                    sa_info,
                    scopes=["https://www.googleapis.com/auth/firebase.messaging"]
                )
                if self.project_id:
                    self.use_v1 = True
            except Exception as e:
                print(f"❌ Error leyendo FCM_SERVICE_ACCOUNT_JSON: {e}")
        self.enabled = os.getenv("FCM_ENABLED", "false").lower() == "true" and (self.use_v1 or bool(self.server_key))
    
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
            if self.use_v1:
                return self._send_v1(device_token, title, body, data or {})
            return self._send_legacy(device_token, title, body, data or {})
        except Exception as e:
            print(f"❌ Error enviando notificación push: {e}")
            return False

    def _send_legacy(self, device_token: str, title: str, body: str, data: Dict[str, Any]) -> bool:
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
            "data": data
        }
        
        response = requests.post(self.api_url, json=payload, headers=headers)
        if response.status_code == 200:
            print(f"✅ Notificación push enviada a {device_token}: {title}")
            return True
        print(f"❌ Error enviando notificación push: {response.status_code} - {response.text}")
        return False

    def _send_v1(self, device_token: str, title: str, body: str, data: Dict[str, Any]) -> bool:
        if not self.credentials or not self.project_id:
            print("❌ Credenciales FCM V1 no configuradas")
            return False
        self.credentials.refresh(Request())
        access_token = self.credentials.token
        url = f"https://fcm.googleapis.com/v1/projects/{self.project_id}/messages:send"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "message": {
                "token": device_token,
                "notification": {
                    "title": title,
                    "body": body,
                },
                "android": {
                    "notification": {
                        "sound": "default"
                    }
                },
                "data": {k: str(v) for k, v in data.items()}
            }
        }
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print(f"✅ Notificación push enviada (v1) a {device_token}: {title}")
            return True
        print(f"❌ Error FCM v1: {response.status_code} - {response.text}")
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

