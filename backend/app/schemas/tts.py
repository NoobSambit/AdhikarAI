from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.agent import ALLOWED_LANGUAGE_CODES

LanguageCode = Literal["en", "hi", "bn", "te", "mr", "ta", "gu", "kn", "ml", "pa", "or"]
TtsProviderName = Literal["local_indictts", "google"]


class TtsRequestModel(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    language_code: LanguageCode
    speaking_rate: float = Field(default=1.0)

    @field_validator("language_code")
    @classmethod
    def validate_language(cls, value: str) -> str:
        if value not in ALLOWED_LANGUAGE_CODES:
            raise ValueError("Unsupported language code.")
        return value

    @field_validator("speaking_rate")
    @classmethod
    def validate_speaking_rate(cls, value: float) -> float:
        allowed = {0.75, 1.0, 1.5}
        if value not in allowed:
            raise ValueError("speaking_rate must be one of 0.75, 1.0, or 1.5.")
        return value


class TtsResponseModel(BaseModel):
    audio_url: str
    audio_mime_type: str
    provider: TtsProviderName
    cached: bool = False
