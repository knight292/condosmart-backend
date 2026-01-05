import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import os
from datetime import datetime

class EmailService:
    def __init__(self):
        # Configuración SMTP (puede ser Gmail, SendGrid, etc.)
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_user)
        self.enabled = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """Envía un email"""
        if not self.enabled:
            print(f"📧 Email deshabilitado. Se enviaría a {to_email}: {subject}")
            return True
        
        if not self.smtp_user or not self.smtp_password:
            print(f"⚠️ SMTP no configurado. Se enviaría a {to_email}: {subject}")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            if text_body:
                part1 = MIMEText(text_body, 'plain')
                msg.attach(part1)
            
            part2 = MIMEText(html_body, 'html')
            msg.attach(part2)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            print(f"✅ Email enviado a {to_email}: {subject}")
            return True
        except Exception as e:
            print(f"❌ Error enviando email a {to_email}: {e}")
            return False
    
    def send_shift_assigned_email(
        self,
        guard_email: str,
        guard_name: str,
        shift_date: datetime,
        shift_type: str,
        assigned_by: str
    ) -> bool:
        """Envía email cuando se asigna un turno"""
        shift_type_label = {
            "morning": "Mañana",
            "afternoon": "Tarde",
            "night": "Noche",
            "full_day": "Día Completo"
        }.get(shift_type, shift_type)
        
        date_str = shift_date.strftime("%d/%m/%Y %H:%M")
        
        subject = f"Turno Asignado - {date_str}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Nuevo Turno Asignado</h2>
            <p>Hola {guard_name},</p>
            <p>Se te ha asignado un nuevo turno:</p>
            <ul>
                <li><strong>Fecha y Hora:</strong> {date_str}</li>
                <li><strong>Tipo de Turno:</strong> {shift_type_label}</li>
                <li><strong>Asignado por:</strong> {assigned_by}</li>
            </ul>
            <p>Por favor, confirma tu asistencia en la aplicación CondoSmart.</p>
            <p>Saludos,<br>Equipo CondoSmart</p>
        </body>
        </html>
        """
        
        text_body = f"""
        Nuevo Turno Asignado
        
        Hola {guard_name},
        
        Se te ha asignado un nuevo turno:
        - Fecha y Hora: {date_str}
        - Tipo de Turno: {shift_type_label}
        - Asignado por: {assigned_by}
        
        Por favor, confirma tu asistencia en la aplicación CondoSmart.
        
        Saludos,
        Equipo CondoSmart
        """
        
        return self.send_email(guard_email, subject, html_body, text_body)
    
    def send_shift_reminder_email(
        self,
        guard_email: str,
        guard_name: str,
        shift_date: datetime,
        shift_type: str
    ) -> bool:
        """Envía email de recordatorio antes del turno"""
        shift_type_label = {
            "morning": "Mañana",
            "afternoon": "Tarde",
            "night": "Noche",
            "full_day": "Día Completo"
        }.get(shift_type, shift_type)
        
        date_str = shift_date.strftime("%d/%m/%Y %H:%M")
        
        subject = f"Recordatorio: Tu turno es mañana - {date_str}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Recordatorio de Turno</h2>
            <p>Hola {guard_name},</p>
            <p>Este es un recordatorio de que tienes un turno programado:</p>
            <ul>
                <li><strong>Fecha y Hora:</strong> {date_str}</li>
                <li><strong>Tipo de Turno:</strong> {shift_type_label}</li>
            </ul>
            <p>Por favor, asegúrate de estar presente a tiempo.</p>
            <p>Saludos,<br>Equipo CondoSmart</p>
        </body>
        </html>
        """
        
        text_body = f"""
        Recordatorio de Turno
        
        Hola {guard_name},
        
        Este es un recordatorio de que tienes un turno programado:
        - Fecha y Hora: {date_str}
        - Tipo de Turno: {shift_type_label}
        
        Por favor, asegúrate de estar presente a tiempo.
        
        Saludos,
        Equipo CondoSmart
        """
        
        return self.send_email(guard_email, subject, html_body, text_body)
    
    def send_shift_swap_notification_email(
        self,
        admin_email: str,
        requester_name: str,
        shift_date: datetime,
        shift_type: str
    ) -> bool:
        """Envía email a admin cuando hay una solicitud de intercambio"""
        shift_type_label = {
            "morning": "Mañana",
            "afternoon": "Tarde",
            "night": "Noche",
            "full_day": "Día Completo"
        }.get(shift_type, shift_type)
        
        date_str = shift_date.strftime("%d/%m/%Y %H:%M")
        
        subject = f"Solicitud de Intercambio de Turno - {date_str}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Solicitud de Intercambio de Turno</h2>
            <p>Hola,</p>
            <p>{requester_name} ha solicitado un intercambio de turno:</p>
            <ul>
                <li><strong>Fecha y Hora:</strong> {date_str}</li>
                <li><strong>Tipo de Turno:</strong> {shift_type_label}</li>
            </ul>
            <p>Por favor, revisa la solicitud en la aplicación CondoSmart.</p>
            <p>Saludos,<br>Equipo CondoSmart</p>
        </body>
        </html>
        """
        
        return self.send_email(admin_email, subject, html_body)

