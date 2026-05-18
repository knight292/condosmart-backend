from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import Condominium, User
from app.models.uuid_helper import USE_SQLITE
from app.schemas.condominium_settings import (
    CondominiumConfigResponse,
    CondominiumSettingsData,
    CondominiumSettingsUpdate,
)
from app.services.condominium_settings import (
    AVAILABLE_MODULES,
    apply_default_settings,
    get_effective_settings,
    parse_settings,
    serialize_settings,
    validate_settings_patch,
    deep_merge,
)

router = APIRouter()


def _get_condominium_or_404(db: Session, condominium_id) -> Condominium:
    search_id = str(condominium_id) if USE_SQLITE else condominium_id
    condo = db.query(Condominium).filter(Condominium.id == search_id).first()
    if not condo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condominium not found",
        )
    return condo


def _can_view_config(user: User, condominium: Condominium) -> bool:
    if user.role == "super_admin":
        return True
    if user.role == "owner" and user.owner_id and condominium.owner_id:
        if USE_SQLITE:
            return str(user.owner_id) == str(condominium.owner_id)
        return user.owner_id == condominium.owner_id
    if user.role in ("admin", "resident", "guard") and user.condominium_id:
        if USE_SQLITE:
            return str(user.condominium_id) == str(condominium.id)
        return user.condominium_id == condominium.id
    return False


def _can_edit_config(user: User, condominium: Condominium) -> bool:
    if user.role == "super_admin":
        return True
    if user.role == "admin" and user.condominium_id:
        if USE_SQLITE:
            return str(user.condominium_id) == str(condominium.id)
        return user.condominium_id == condominium.id
    if user.role == "owner" and user.owner_id and condominium.owner_id:
        if USE_SQLITE:
            return str(user.owner_id) == str(condominium.owner_id)
        return user.owner_id == condominium.owner_id
    return False


def _build_config_response(condominium: Condominium) -> CondominiumConfigResponse:
    settings = get_effective_settings(condominium)
    return CondominiumConfigResponse(
        condominium_id=condominium.id,
        condominium_name=condominium.name,
        subscription_plan=condominium.subscription_plan,
        subscription_status=condominium.subscription_status,
        settings=CondominiumSettingsData(**settings),
        available_modules=AVAILABLE_MODULES,
    )


@router.get("/modules-catalog")
def get_modules_catalog():
    """Catálogo de módulos que se pueden activar/desactivar por condominio."""
    return {"modules": AVAILABLE_MODULES}


@router.get("/my-config", response_model=CondominiumConfigResponse)
def get_my_condominium_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Configuración del condominio del usuario autenticado."""
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not assigned to a condominium",
        )

    condominium = _get_condominium_or_404(db, current_user.condominium_id)
    if not _can_view_config(current_user, condominium):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to view this condominium configuration",
        )

    apply_default_settings(condominium)
    return _build_config_response(condominium)


@router.get("/{condominium_id}/config", response_model=CondominiumConfigResponse)
def get_condominium_config(
    condominium_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    condominium = _get_condominium_or_404(db, condominium_id)
    if not _can_view_config(current_user, condominium):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to view this condominium configuration",
        )

    apply_default_settings(condominium)
    return _build_config_response(condominium)


@router.put("/{condominium_id}/config", response_model=CondominiumConfigResponse)
def update_condominium_config(
    condominium_id: UUID,
    update_data: CondominiumSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Actualiza parcialmente la configuración de un condominio."""
    condominium = _get_condominium_or_404(db, condominium_id)
    if not _can_edit_config(current_user, condominium):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin, owner or super_admin can update condominium configuration",
        )

    patch = validate_settings_patch(update_data.to_patch_dict())
    if not patch:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid configuration fields provided",
        )

    current = parse_settings(condominium.settings)
    merged = deep_merge(current, patch)
    condominium.settings = serialize_settings(merged)
    db.commit()
    db.refresh(condominium)

    return _build_config_response(condominium)
