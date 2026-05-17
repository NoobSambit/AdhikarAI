from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.voice import LanguageCode

ChecklistStatus = Literal["not_gathered", "gathered", "verified", "rejected"]
ApplicationStatusValue = Literal["not_started", "documents_gathering", "submitted", "pending", "approved", "rejected"]
FontSize = Literal["default", "large", "extra_large"]


class SendOtpRequest(BaseModel):
    organisation_id: UUID
    phone_e164: str = Field(pattern=r"^\+[1-9]\d{7,14}$")


class SendOtpResponse(BaseModel):
    challenge_id: UUID
    masked_phone: str
    retry_after_seconds: int


class VerifyOtpRequest(BaseModel):
    organisation_id: UUID
    challenge_id: UUID
    otp: str = Field(min_length=4, max_length=8)
    guest_profile_id: str | None = None
    language_code: LanguageCode = "hi"


class AuthUserModel(BaseModel):
    id: UUID
    phone_e164: str
    language_code: str
    primary_profile_id: UUID | None = None
    high_contrast_enabled: bool = False
    font_size: FontSize = "default"
    notification_opt_in: bool = False


class VerifyOtpResponse(BaseModel):
    user: AuthUserModel
    migrated_guest_profile: bool


class MeResponse(BaseModel):
    user: AuthUserModel
    primary_profile: dict[str, Any] | None = None


class UpdateProfileSettingsRequest(BaseModel):
    language_code: LanguageCode | None = None
    high_contrast_enabled: bool | None = None
    font_size: FontSize | None = None
    notification_opt_in: bool | None = None
    guest_profile_id: str | None = None


class SaveSchemeRequest(BaseModel):
    profile_id: UUID
    scheme_id: str


class SaveSchemeResponse(BaseModel):
    saved: bool
    reminder_scheduled_at: datetime


class UpdateChecklistRequest(BaseModel):
    profile_id: UUID
    scheme_id: str
    document_name: str = Field(min_length=1)
    status: ChecklistStatus
    idempotency_key: str = Field(min_length=8)
    accepted_substitutes: list[dict[str, Any]] = Field(default_factory=list)
    is_mandatory: bool = True


class ChecklistItemView(BaseModel):
    document_name: str
    is_mandatory: bool
    status: ChecklistStatus
    accepted_substitutes: list[dict[str, Any]] = Field(default_factory=list)


class ChecklistResponse(BaseModel):
    profile_id: UUID
    scheme_id: str
    items: list[ChecklistItemView]
    ready_to_apply: bool
    substitute_guidance: list[dict[str, Any]] = Field(default_factory=list)


class UpdateApplicationStatusRequest(BaseModel):
    profile_id: UUID
    scheme_id: str
    status: ApplicationStatusValue
    notes: str | None = Field(default=None, max_length=500)


class ApplicationStatusResponse(BaseModel):
    profile_id: UUID
    scheme_id: str
    status: ApplicationStatusValue
    reminder_scheduled_for: datetime | None = None


class PushSubscriptionRequest(BaseModel):
    endpoint: str
    keys: dict[str, str]
    user_agent: str | None = None

    @field_validator("keys")
    @classmethod
    def require_vapid_keys(cls, value: dict[str, str]) -> dict[str, str]:
        if not value.get("p256dh") or not value.get("auth"):
            raise ValueError("Push subscription keys are incomplete.")
        return value


class PushSubscriptionResponse(BaseModel):
    subscribed: bool


class ActionPlanRequest(BaseModel):
    profile_id: UUID
    conversation_session_id: UUID | None = None
    scheme_ids: list[str] = Field(min_length=1)
    format: Literal["pdf", "image", "whatsapp_text"] = "whatsapp_text"


class ActionPlanResponse(BaseModel):
    action_plan_id: UUID
    format: str
    share_url: str
    content: dict[str, Any]


class OfflineSyncItem(BaseModel):
    action_type: str
    payload: dict[str, Any]
    created_at: datetime
    retry_count: int = Field(default=0, ge=0, le=5)
    idempotency_key: str = Field(min_length=8)


class OfflineSyncRequest(BaseModel):
    events: list[OfflineSyncItem]


class OfflineSyncResult(BaseModel):
    idempotency_key: str
    status: Literal["applied", "duplicate", "failed"]
    error_code: str | None = None


class OfflineSyncResponse(BaseModel):
    results: list[OfflineSyncResult]


class DigiLockerStartRequest(BaseModel):
    profile_id: UUID
    redirect_uri: str


class DigiLockerStartResponse(BaseModel):
    authorization_url: str
    state: str


class DigiLockerCallbackResponse(BaseModel):
    status: Literal["connected", "failed"]
    verified_documents: list[dict[str, Any]] = Field(default_factory=list)


class AadhaarPrefillStartRequest(BaseModel):
    profile_id: UUID
    consent: bool


class AadhaarPrefillStartResponse(BaseModel):
    status: Literal["ready", "blocked"]
    allowed_fields: list[str]
