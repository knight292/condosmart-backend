#!/usr/bin/env python3
"""
Script para generar códigos de licencia de CondoSmart

Uso:
    python generar_licencia.py --package basic --buyer "Juan Pérez" --email "juan@example.com"
    python generar_licencia.py --package intermediate --buyer "María González"
    python generar_licencia.py --package premium --buyer "Carlos Rodríguez" --price 80000
"""

import argparse
import sys
import os

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import License
from app.routers.licenses import generate_license_code, PACKAGE_CONFIG
from app.schemas.license import LicenseCreate
from datetime import datetime

def generate_license(
    package_type: str,
    buyer_name: str = None,
    buyer_email: str = None,
    purchase_price: int = None,
    notes: str = None
):
    """Genera una nueva licencia"""
    
    if package_type not in PACKAGE_CONFIG:
        print(f"❌ Error: Tipo de paquete inválido. Opciones: {list(PACKAGE_CONFIG.keys())}")
        return None
    
    config = PACKAGE_CONFIG[package_type]
    
    # Generar código único
    code = generate_license_code()
    db = SessionLocal()
    
    # Verificar que no exista
    while db.query(License).filter(License.code == code).first():
        code = generate_license_code()
    
    # Crear licencia
    license_data = LicenseCreate(
        package_type=package_type,
        max_units=config["max_units"],
        max_users=config["max_users"],
        purchase_price=purchase_price or config["price"],
        buyer_name=buyer_name,
        buyer_email=buyer_email,
        notes=notes
    )
    
    new_license = License(
        code=code,
        package_type=license_data.package_type,
        max_units=license_data.max_units,
        max_users=license_data.max_users,
        purchase_price=license_data.purchase_price,
        buyer_name=license_data.buyer_name,
        buyer_email=license_data.buyer_email,
        notes=license_data.notes,
        activated=False
    )
    
    db.add(new_license)
    db.commit()
    db.refresh(new_license)
    
    print("\n" + "="*60)
    print("✅ LICENCIA GENERADA EXITOSAMENTE")
    print("="*60)
    print(f"\n📋 Código de Licencia: {code}")
    print(f"📦 Paquete: {package_type.upper()}")
    print(f"💰 Precio: ${config['price']:,} MXN")
    print(f"🏢 Unidades máximas: {config['max_units'] or 'Ilimitadas'}")
    print(f"👥 Usuarios máximos: {config['max_users'] or 'Ilimitados'}")
    if buyer_name:
        print(f"👤 Comprador: {buyer_name}")
    if buyer_email:
        print(f"📧 Email: {buyer_email}")
    print(f"\n📝 Estado: {'Activa' if new_license.activated else 'Pendiente de activación'}")
    print("\n" + "="*60)
    print("\n💡 Instrucciones:")
    print(f"   1. Comparte este código con el cliente: {code}")
    print("   2. El cliente debe descargar la app")
    print("   3. El cliente debe iniciar sesión o registrarse")
    print("   4. El cliente debe ir a 'Activar Licencia' e ingresar el código")
    print("\n" + "="*60 + "\n")
    
    db.close()
    return new_license

def list_licenses():
    """Lista todas las licencias"""
    db = SessionLocal()
    licenses = db.query(License).order_by(License.created_at.desc()).all()
    
    if not licenses:
        print("No hay licencias generadas aún.")
        db.close()
        return
    
    print("\n" + "="*80)
    print("📋 LISTA DE LICENCIAS")
    print("="*80)
    print(f"\n{'Código':<20} {'Paquete':<15} {'Estado':<15} {'Comprador':<25} {'Fecha':<15}")
    print("-"*80)
    
    for lic in licenses:
        status = "✅ Activada" if lic.activated else "⏳ Pendiente"
        buyer = lic.buyer_name or "N/A"
        date = lic.created_at.strftime("%Y-%m-%d")
        print(f"{lic.code:<20} {lic.package_type:<15} {status:<15} {buyer:<25} {date:<15}")
    
    print("="*80 + "\n")
    db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generar códigos de licencia para CondoSmart')
    parser.add_argument('--package', '-p', 
                       choices=['basic', 'intermediate', 'premium'],
                       required=True,
                       help='Tipo de paquete (basic, intermediate, premium)')
    parser.add_argument('--buyer', '-b',
                       help='Nombre del comprador')
    parser.add_argument('--email', '-e',
                       help='Email del comprador')
    parser.add_argument('--price', type=int,
                       help='Precio personalizado (opcional)')
    parser.add_argument('--notes', '-n',
                       help='Notas adicionales')
    parser.add_argument('--list', '-l',
                       action='store_true',
                       help='Listar todas las licencias')
    
    args = parser.parse_args()
    
    if args.list:
        list_licenses()
    else:
        generate_license(
            package_type=args.package,
            buyer_name=args.buyer,
            buyer_email=args.email,
            purchase_price=args.price,
            notes=args.notes
        )

