"""Dependencias FastAPI para validar módulos habilitados por condominio."""
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import Condominium, User
from app.models.uuid_helper import USE_SQLITE
from app.services.condominium_settings import AVAILABLE_MODULES, is_module_enabled


def resolve_condominium_id(user: User, request: Request):
    """Obtiene el condominio activo del usuario o del header (owners)."""
    if user.condominium_id:
        return user.condominium_id
    if user.role == "owner":
        header_id = request.headers.get("X-Condominium-ID")
        if header_id:
            return header_id
    return None


def require_module(module_key: str):
    """Bloquea el endpoint si el módulo está desactivado en el condominio."""

    def dependency(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> None:
        if current_user.role == "super_admin":
            return

        condo_id = resolve_condominium_id(current_user, request)
        if not condo_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must belong to a condominium",
            )

        search_id = str(condo_id) if USE_SQLITE else condo_id
        condominium = (
            db.query(Condominium).filter(Condominium.id == search_id).first()
        )
        if not condominium:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Condominium not found",
            )

        if current_user.role == "owner" and condominium.owner_id:
            if USE_SQLITE:
                owner_ok = str(current_user.owner_id) == str(condominium.owner_id)
            else:
                owner_ok = current_user.owner_id == condominium.owner_id
            if not owner_ok:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Condominium does not belong to this owner",
                )

        if not is_module_enabled(condominium, module_key):
            label = AVAILABLE_MODULES.get(module_key, module_key)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"El módulo '{label}' no está habilitado en este condominio",
            )

    return dependency
