import json

from app.schemas.voice import AsrResponseModel, BrowserAsrInputModel


class BrowserASRProvider:
    async def transcribe(self, audio: bytes, mime_type: str, language_hint: str | None) -> AsrResponseModel:
        payload = BrowserAsrInputModel.model_validate(json.loads(audio.decode("utf-8")))
        return AsrResponseModel(
            transcript=payload.transcript,
            detected_language_code=payload.detected_language_code or language_hint or "en",
            confidence=payload.confidence,
            duration_ms=payload.duration_ms,
            provider="browser",
            confidence_method="browser",
        )
