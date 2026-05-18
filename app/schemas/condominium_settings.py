from typing import Any, Dict, Optional

from pydantic import BaseModel, Field
from uuid import UUID


class BrandingSettings(BaseModel):
    display_name: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: str = "#1976D2"
    secondary_color: str = "#FFFFFF"


class LocaleSettings(BaseModel):
    timezone: str = "America/Mexico_City"
    language: str = "es"
    currency: str = "MXN"


class AccessSettings(BaseModel):
    gate_open_time: str = "06:00"
    gate_close_time: str = "22:00"
    visits_require_preregistration: bool = True
    visits_qr_required: bool = True


class NotificationSettings(BaseModel):
    push_enabled: bool = True
    email_enabled: bool = False


class CondominiumSettingsData(BaseModel):
    branding: BrandingSettings
    locale: LocaleSettings
    access: AccessSettings
    modules: Dict[str, bool]
    notifications: NotificationSettings


class CondominiumConfigResponse(BaseModel):
    condominium_id: UUID
    condominium_name: str
    subscription_plan: Optional[str] = None
    subscription_status: Optional[str] = None
    settings: CondominiumSettingsData
    available_modules: Dict[str, str] = Field(
        default_factory=dict,
        description="Catálogo de módulos configurables",
    )


class CondominiumSettingsUpdate(BaseModel):
    branding: Optional[BrandingSettings] = None
    locale: Optional[LocaleSettings] = None
    access: Optional[AccessSettings] = None
    modules: Optional[Dict[str, bool]] = None
    notifications: Optional[NotificationSettings] = None

    def to_patch_dict(self) -> Dict[str, Any]:
        data = self.model_dump(exclude_none=True)
        return {k: v for k, v in data.items() if v is not None}
