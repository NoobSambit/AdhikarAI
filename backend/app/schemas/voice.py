from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.agent import ALLOWED_LANGUAGE_CODES

LanguageCode = Literal["en", "hi", "bn", "te", "mr", "ta", "gu", "kn", "ml", "pa", "or"]
VoiceProviderName = Literal["local", "groq", "browser"]


def _validate_language(value: str) -> str:
    if value not in ALLOWED_LANGUAGE_CODES:
        raise ValueError("Unsupported language code.")
    return value


class AsrResponseModel(BaseModel):
    transcript: str
    detected_language_code: LanguageCode
    confidence: float = Field(ge=0, le=1)
    duration_ms: int = Field(ge=0)
    provider: VoiceProviderName
    confidence_method: str | None = None

    @field_validator("detected_language_code")
    @classmethod
    def validate_detected_language(cls, value: str) -> str:
        return _validate_language(value)


class BrowserAsrInputModel(BaseModel):
    transcript: str = Field(min_length=1, max_length=2000)
    detected_language_code: LanguageCode = "en"
    confidence: float = Field(default=0.85, ge=0, le=1)
    duration_ms: int = Field(default=0, ge=0)


class VoiceTurnRequestModel(BaseModel):
    organisation_id: UUID
    session_id: str
    selected_language_code: LanguageCode
    client_duration_ms: int | None = Field(default=None, ge=0)

    @field_validator("selected_language_code")
    @classmethod
    def validate_selected_language(cls, value: str) -> str:
        return _validate_language(value)


class VoiceTurnResponseModel(BaseModel):
    type: Literal["transcript", "low_confidence", "result", "question", "clarification", "error"]
    transcript: str | None = None
    detected_language_code: LanguageCode | None = None
    selected_language_code: LanguageCode
    confidence: float | None = Field(default=None, ge=0, le=1)
    content: str
    profile_completeness: int = Field(ge=0, le=100)
    audio_url: str | None = None
    timings: dict[str, int]
    payload: dict[str, Any] | None = None


class VoiceWsStartMessageModel(BaseModel):
    type: Literal["start"]
    session_id: str
    organisation_id: UUID
    selected_language_code: LanguageCode
    mime_type: str


class VoiceWsEndMessageModel(BaseModel):
    type: Literal["end"]


class VoiceWsStatusMessageModel(BaseModel):
    type: Literal["partial_status", "error"]
    stage: str | None = None
    content: str
    payload: dict[str, Any] | None = None
