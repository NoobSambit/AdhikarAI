from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.agent import ALLOWED_LANGUAGE_CODES

LanguageCode = Literal["en", "hi", "bn", "te", "mr", "ta", "gu", "kn", "ml", "pa", "or"]
TranslationProviderName = Literal["local_indictrans2", "ai4bharat_hosted", "google"]


class TranslateRequestModel(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    source_lang: LanguageCode
    target_lang: LanguageCode

    @field_validator("source_lang", "target_lang")
    @classmethod
    def validate_language(cls, value: str) -> str:
        if value not in ALLOWED_LANGUAGE_CODES:
            raise ValueError("Unsupported language code.")
        return value


class TranslateResponseModel(BaseModel):
    translated_text: str
    source_lang: LanguageCode
    target_lang: LanguageCode
    provider: TranslationProviderName
    cached: bool = False
    warning_code: str | None = None
