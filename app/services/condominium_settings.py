"""Configuración por condominio: valores por defecto, merge y validación."""
from __future__ import annotations

import copy
import json
from typing import Any, Dict, Optional

from app.models.condominium import Condominium

AVAILABLE_MODULES: Dict[str, str] = {
    "payments": "Pagos y cuotas",
    "tickets": "Tickets e incidencias",
    "visits": "Visitas y acceso",
    "reservations": "Reservas de áreas comunes",
    "announcements": "Avisos",
    "messages": "Chat interno",
    "documents": "Documentos",
    "maintenance": "Mantenimiento",
    "contracts": "Contratos",
    "inventory": "Inventario",
    "regulations": "Reglamento",
    "packages": "Paquetería",
    "guard_shifts": "Turnos de guardias",
    "recurring_payments": "Pagos recurrentes",
}

DEFAULT_CONDOMINIUM_SETTINGS: Dict[str, Any] = {
    "branding": {
        "display_name": None,
        "logo_url": None,
        "primary_color": "#1976D2",
        "secondary_color": "#FFFFFF",
    },
    "locale": {
        "timezone": "America/Mexico_City",
        "language": "es",
        "currency": "MXN",
    },
    "access": {
        "gate_open_time": "06:00",
        "gate_close_time": "22:00",
        "visits_require_preregistration": True,
        "visits_qr_required": True,
    },
    "modules": {key: True for key in AVAILABLE_MODULES},
    "notifications": {
        "push_enabled": True,
        "email_enabled": False,
    },
}


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Combina diccionarios anidados sin perder claves del base."""
    result = copy.deepcopy(base)
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def parse_settings(raw: Optional[str]) -> Dict[str, Any]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def get_effective_settings(condominium: Condominium) -> Dict[str, Any]:
    """Configuración final del condominio (defaults + personalización)."""
    stored = parse_settings(condominium.settings)
    merged = deep_merge(DEFAULT_CONDOMINIUM_SETTINGS, stored)
    if condominium.name and not merged["branding"].get("display_name"):
        merged["branding"]["display_name"] = condominium.name
    return merged


def serialize_settings(settings: Dict[str, Any]) -> str:
    return json.dumps(settings, ensure_ascii=False)


def apply_default_settings(condominium: Condominium) -> None:
    """Asigna configuración por defecto si el condominio no tiene ninguna."""
    if not condominium.settings:
        effective = get_effective_settings(condominium)
        condominium.settings = serialize_settings(effective)


def is_module_enabled(condominium: Condominium, module_key: str) -> bool:
    settings = get_effective_settings(condominium)
    modules = settings.get("modules", {})
    return bool(modules.get(module_key, True))


def validate_settings_patch(patch: Dict[str, Any]) -> Dict[str, Any]:
    """Valida y normaliza un parche parcial de configuración."""
    cleaned: Dict[str, Any] = {}

    if "branding" in patch and isinstance(patch["branding"], dict):
        branding = {}
        for key in ("display_name", "logo_url", "primary_color", "secondary_color"):
            if key in patch["branding"]:
                branding[key] = patch["branding"][key]
        cleaned["branding"] = branding

    if "locale" in patch and isinstance(patch["locale"], dict):
        locale = {}
        for key in ("timezone", "language", "currency"):
            if key in patch["locale"]:
                locale[key] = patch["locale"][key]
        cleaned["locale"] = locale

    if "access" in patch and isinstance(patch["access"], dict):
        access = {}
        for key in (
            "gate_open_time",
            "gate_close_time",
            "visits_require_preregistration",
            "visits_qr_required",
        ):
            if key in patch["access"]:
                access[key] = patch["access"][key]
        cleaned["access"] = access

    if "modules" in patch and isinstance(patch["modules"], dict):
        modules = {}
        for key, value in patch["modules"].items():
            if key in AVAILABLE_MODULES and isinstance(value, bool):
                modules[key] = value
        cleaned["modules"] = modules

    if "notifications" in patch and isinstance(patch["notifications"], dict):
        notifications = {}
        for key in ("push_enabled", "email_enabled"):
            if key in patch["notifications"] and isinstance(
                patch["notifications"][key], bool
            ):
                notifications[key] = patch["notifications"][key]
        cleaned["notifications"] = notifications

    return cleaned
