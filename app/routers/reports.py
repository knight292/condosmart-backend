from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta, date
from io import BytesIO
import csv
from app.db import get_db
from app.models import GuardShift, User, Condominium
from app.models.uuid_helper import USE_SQLITE
from app.auth import get_current_user
from app.routers.guard_shifts import _calculate_shift_times

router = APIRouter()

@router.get("/shifts/pdf")
def export_shifts_pdf(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Exporta turnos a PDF"""
    if current_user.role not in ["admin", "super_admin", "owner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can export reports"
        )
    
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    # Convertir condominium_id a string si es SQLite
    if USE_SQLITE:
        condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
    else:
        condo_id = current_user.condominium_id
    
    # Obtener turnos
    query = db.query(GuardShift).filter(
        GuardShift.condominium_id == condo_id
    )
    
    if start_date:
        query = query.filter(GuardShift.shift_date >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(GuardShift.shift_date <= datetime.combine(end_date, datetime.max.time()))
    
    shifts = query.order_by(GuardShift.shift_date.asc()).all()
    
    # Generar HTML simple (se puede mejorar con reportlab)
    html_content = _generate_pdf_html(shifts, current_user, db)
    
    # Retornar como PDF (en producción usar reportlab o weasyprint)
    return StreamingResponse(
        BytesIO(html_content.encode()),
        media_type="text/html",
        headers={
            "Content-Disposition": f"attachment; filename=horarios_{datetime.now().strftime('%Y%m%d')}.html"
        }
    )

@router.get("/shifts/excel")
def export_shifts_excel(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Exporta turnos a Excel (CSV)"""
    if current_user.role not in ["admin", "super_admin", "owner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can export reports"
        )
    
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    # Convertir condominium_id a string si es SQLite
    if USE_SQLITE:
        condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
    else:
        condo_id = current_user.condominium_id
    
    # Obtener turnos
    query = db.query(GuardShift).filter(
        GuardShift.condominium_id == condo_id
    )
    
    if start_date:
        query = query.filter(GuardShift.shift_date >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(GuardShift.shift_date <= datetime.combine(end_date, datetime.max.time()))
    
    shifts = query.order_by(GuardShift.shift_date.asc()).all()
    
    # Generar CSV
    output = BytesIO()
    writer = csv.writer(output)
    
    # Encabezados
    writer.writerow([
        "Fecha",
        "Hora Inicio",
        "Hora Fin",
        "Guardia",
        "Tipo de Turno",
        "Estado",
        "Check-in",
        "Check-out"
    ])
    
    # Datos
    for shift in shifts:
        # Convertir ID para la query si es SQLite
        if USE_SQLITE:
            guard_search_id = str(shift.guard_id) if shift.guard_id else None
        else:
            guard_search_id = shift.guard_id
        
        guard = db.query(User).filter(User.id == guard_search_id).first() if guard_search_id else None
        shift_start, shift_end = _calculate_shift_times(shift.shift_date, shift.shift_type)
        
        writer.writerow([
            shift.shift_date.strftime("%Y-%m-%d"),
            shift_start.strftime("%H:%M"),
            shift_end.strftime("%H:%M"),
            guard.full_name if guard else "N/A",
            shift.shift_type,
            shift.status,
            shift.check_in_time.strftime("%Y-%m-%d %H:%M") if shift.check_in_time else "",
            shift.check_out_time.strftime("%Y-%m-%d %H:%M") if shift.check_out_time else "",
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=horarios_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )

def _generate_pdf_html(shifts, current_user, db):
    """Genera HTML para PDF (simplificado)"""
    # Convertir condominium_id a string si es SQLite
    if USE_SQLITE:
        condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
    else:
        condo_id = current_user.condominium_id
    
    condo = db.query(Condominium).filter(Condominium.id == condo_id).first() if condo_id else None
    condo_name = condo.name if condo else "Condominio"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Reporte de Horarios - {condo_name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #333; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #4CAF50; color: white; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>Reporte de Horarios - {condo_name}</h1>
        <p>Generado el: {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
        <p>Total de turnos: {len(shifts)}</p>
        <table>
            <tr>
                <th>Fecha</th>
                <th>Hora Inicio</th>
                <th>Hora Fin</th>
                <th>Guardia</th>
                <th>Tipo</th>
                <th>Estado</th>
            </tr>
    """
    
    # Importar función de cálculo
    from app.routers.guard_shifts import _calculate_shift_times
    
    for shift in shifts:
        # Convertir ID para la query si es SQLite
        if USE_SQLITE:
            guard_search_id = str(shift.guard_id) if shift.guard_id else None
        else:
            guard_search_id = shift.guard_id
        
        guard = db.query(User).filter(User.id == guard_search_id).first() if guard_search_id else None
        shift_start, shift_end = _calculate_shift_times(shift.shift_date, shift.shift_type)
        
        shift_type_label = {
            "morning": "Mañana",
            "afternoon": "Tarde",
            "night": "Noche",
            "full_day": "Día Completo"
        }.get(shift.shift_type, shift.shift_type)
        
        status_label = {
            "scheduled": "Programado",
            "active": "En Turno",
            "completed": "Completado",
            "cancelled": "Cancelado"
        }.get(shift.status, shift.status)
        
        html += f"""
            <tr>
                <td>{shift.shift_date.strftime("%d/%m/%Y")}</td>
                <td>{shift_start.strftime("%H:%M")}</td>
                <td>{shift_end.strftime("%H:%M")}</td>
                <td>{guard.full_name if guard else "N/A"}</td>
                <td>{shift_type_label}</td>
                <td>{status_label}</td>
            </tr>
        """
    
    html += """
        </table>
    </body>
    </html>
    """
    
    return html

