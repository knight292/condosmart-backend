from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from app.db import get_db
from app.models import Package, User
from app.models.uuid_helper import USE_SQLITE
from app.schemas.package import PackageCreate, PackageUpdate, PackageResponse
from app.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=PackageResponse, status_code=status.HTTP_201_CREATED)
def create_package(
    package_data: PackageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Solo admins, guards o super_admins pueden crear paquetes
    if current_user.role not in ["admin", "guard", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins, guards, or super_admins can create packages"
        )
    
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    # Convertir IDs a string si es SQLite
    if USE_SQLITE:
        condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
        user_id = str(current_user.id) if current_user.id else None
        resident_id = str(package_data.resident_id) if package_data.resident_id else None
    else:
        condo_id = current_user.condominium_id
        user_id = current_user.id
        resident_id = package_data.resident_id
    
    # Verificar que el residente pertenece al mismo condominio
    resident = db.query(User).filter(User.id == resident_id).first()
    if not resident:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resident not found"
        )
    
    # Comparar condominium_id
    resident_condo_id = str(resident.condominium_id) if (USE_SQLITE and resident.condominium_id) else resident.condominium_id
    if resident_condo_id != condo_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resident does not belong to this condominium"
        )
    
    new_package = Package(
        condominium_id=condo_id,
        resident_id=resident_id,
        received_by_id=user_id,
        carrier=package_data.carrier,
        tracking_number=package_data.tracking_number,
        description=package_data.description,
        notes=package_data.notes,
        status="received"
    )
    db.add(new_package)
    db.commit()
    db.refresh(new_package)
    
    return PackageResponse(
        id=new_package.id,
        condominium_id=new_package.condominium_id,
        resident_id=new_package.resident_id,
        resident_name=resident.full_name,
        received_by_id=new_package.received_by_id,
        received_by_name=current_user.full_name,
        carrier=new_package.carrier,
        tracking_number=new_package.tracking_number,
        description=new_package.description,
        status=new_package.status,
        received_at=new_package.received_at,
        picked_up_at=new_package.picked_up_at,
        notes=new_package.notes,
        created_at=new_package.created_at,
        updated_at=new_package.updated_at
    )

@router.get("/", response_model=List[PackageResponse])
def get_packages(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    status_filter: Optional[str] = Query(None, description="Filter by status: pending, received, picked_up, returned")
):
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    # Convertir IDs a string si es SQLite
    if USE_SQLITE:
        condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
        user_id = str(current_user.id) if current_user.id else None
    else:
        condo_id = current_user.condominium_id
        user_id = current_user.id
    
    query = db.query(Package).filter(
        Package.condominium_id == condo_id
    )
    
    # Los residentes solo ven sus propios paquetes
    if current_user.role == "resident":
        query = query.filter(Package.resident_id == user_id)
    
    # Filtrar por estado si se proporciona
    if status_filter:
        query = query.filter(Package.status == status_filter)
    
    packages = query.order_by(Package.received_at.desc()).all()
    
    results = []
    for package in packages:
        # Convertir IDs para las queries si es SQLite
        if USE_SQLITE:
            resident_id = str(package.resident_id) if package.resident_id else None
            received_by_id = str(package.received_by_id) if package.received_by_id else None
        else:
            resident_id = package.resident_id
            received_by_id = package.received_by_id
        
        resident = db.query(User).filter(User.id == resident_id).first() if resident_id else None
        received_by = db.query(User).filter(User.id == received_by_id).first() if received_by_id else None
        
        results.append(PackageResponse(
            id=package.id,
            condominium_id=package.condominium_id,
            resident_id=package.resident_id,
            resident_name=resident.full_name if resident else "Unknown",
            received_by_id=package.received_by_id,
            received_by_name=received_by.full_name if received_by else None,
            carrier=package.carrier,
            tracking_number=package.tracking_number,
            description=package.description,
            status=package.status,
            received_at=package.received_at,
            picked_up_at=package.picked_up_at,
            notes=package.notes,
            created_at=package.created_at,
            updated_at=package.updated_at
        ))
    
    return results

@router.get("/{package_id}", response_model=PackageResponse)
def get_package(
    package_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    package = db.query(Package).filter(Package.id == package_id).first()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )
    
    # Convertir IDs a string si es SQLite para comparaciones
    if USE_SQLITE:
        condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
        user_id = str(current_user.id) if current_user.id else None
        package_condo_id = str(package.condominium_id) if package.condominium_id else None
        package_resident_id = str(package.resident_id) if package.resident_id else None
    else:
        condo_id = current_user.condominium_id
        user_id = current_user.id
        package_condo_id = package.condominium_id
        package_resident_id = package.resident_id
    
    if package_condo_id != condo_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Package does not belong to your condominium"
        )
    
    # Los residentes solo pueden ver sus propios paquetes
    if current_user.role == "resident" and package_resident_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own packages"
        )
    
    # Convertir IDs para las queries si es SQLite
    if USE_SQLITE:
        resident_id = str(package.resident_id) if package.resident_id else None
        received_by_id = str(package.received_by_id) if package.received_by_id else None
    else:
        resident_id = package.resident_id
        received_by_id = package.received_by_id
    
    resident = db.query(User).filter(User.id == resident_id).first() if resident_id else None
    received_by = db.query(User).filter(User.id == received_by_id).first() if received_by_id else None
    
    return PackageResponse(
        id=package.id,
        condominium_id=package.condominium_id,
        resident_id=package.resident_id,
        resident_name=resident.full_name if resident else "Unknown",
        received_by_id=package.received_by_id,
        received_by_name=received_by.full_name if received_by else None,
        carrier=package.carrier,
        tracking_number=package.tracking_number,
        description=package.description,
        status=package.status,
        received_at=package.received_at,
        picked_up_at=package.picked_up_at,
        notes=package.notes,
        created_at=package.created_at,
        updated_at=package.updated_at
    )

@router.patch("/{package_id}", response_model=PackageResponse)
def update_package(
    package_id: UUID,
    package_update: PackageUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    package = db.query(Package).filter(Package.id == package_id).first()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )
    
    # Convertir IDs a string si es SQLite para comparaciones
    if USE_SQLITE:
        condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
        user_id = str(current_user.id) if current_user.id else None
        package_condo_id = str(package.condominium_id) if package.condominium_id else None
        package_resident_id = str(package.resident_id) if package.resident_id else None
    else:
        condo_id = current_user.condominium_id
        user_id = current_user.id
        package_condo_id = package.condominium_id
        package_resident_id = package.resident_id
    
    if package_condo_id != condo_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Package does not belong to your condominium"
        )
    
    # Los residentes solo pueden marcar sus paquetes como recogidos
    if current_user.role == "resident":
        if package_resident_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own packages"
            )
        # Los residentes solo pueden cambiar el estado a "picked_up"
        if package_update.status and package_update.status != "picked_up":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Residents can only mark packages as picked up"
            )
        if package_update.status == "picked_up":
            package.picked_up_at = datetime.utcnow()
    
    # Actualizar campos
    if package_update.status:
        package.status = package_update.status
    if package_update.notes is not None:
        package.notes = package_update.notes
    
    package.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(package)
    
    # Convertir IDs para las queries si es SQLite
    if USE_SQLITE:
        resident_id = str(package.resident_id) if package.resident_id else None
        received_by_id = str(package.received_by_id) if package.received_by_id else None
    else:
        resident_id = package.resident_id
        received_by_id = package.received_by_id
    
    resident = db.query(User).filter(User.id == resident_id).first() if resident_id else None
    received_by = db.query(User).filter(User.id == received_by_id).first() if received_by_id else None
    
    return PackageResponse(
        id=package.id,
        condominium_id=package.condominium_id,
        resident_id=package.resident_id,
        resident_name=resident.full_name if resident else "Unknown",
        received_by_id=package.received_by_id,
        received_by_name=received_by.full_name if received_by else None,
        carrier=package.carrier,
        tracking_number=package.tracking_number,
        description=package.description,
        status=package.status,
        received_at=package.received_at,
        picked_up_at=package.picked_up_at,
        notes=package.notes,
        created_at=package.created_at,
        updated_at=package.updated_at
    )

@router.delete("/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_package(
    package_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Solo admins o super_admins pueden eliminar paquetes
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins or super_admins can delete packages"
        )
    
    package = db.query(Package).filter(Package.id == package_id).first()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )
    
    # Convertir IDs a string si es SQLite para comparaciones
    if USE_SQLITE:
        condo_id = str(current_user.condominium_id) if current_user.condominium_id else None
        package_condo_id = str(package.condominium_id) if package.condominium_id else None
    else:
        condo_id = current_user.condominium_id
        package_condo_id = package.condominium_id
    
    if package_condo_id != condo_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Package does not belong to your condominium"
        )
    
    db.delete(package)
    db.commit()
    
    return None

