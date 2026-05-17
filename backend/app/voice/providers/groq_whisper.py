import httpx

from app.core.config import Settings
from app.core.errors import ApiError
from app.schemas.voice import AsrResponseModel


class GroqWhisperProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def transcribe(self, audio: bytes, mime_type: str, language_hint: str | None) -> AsrResponseModel:
        if not self.settings.groq_api_key:
            raise ApiError(502, "ASR_PROVIDER_ERROR", "Speech service failed. Please try again or type your message.", "audio")
        files = {"file": ("voice", audio, mime_type)}
        data = {"model": self.settings.groq_whisper_model, "response_format": "verbose_json"}
        if language_hint and language_hint != "en":
            data["language"] = language_hint
        try:
            async with httpx.AsyncClient(timeout=self.settings.asr_timeout_seconds) as client:
                response = await client.post(
                    self.settings.groq_transcriptions_url,
                    headers={"Authorization": f"Bearer {self.settings.groq_api_key}"},
                    data=data,
                    files=files,
                )
        except httpx.TimeoutException as exc:
            raise ApiError(504, "ASR_TIMEOUT", "Speech service is slow. Please try again or type your message.", "audio") from exc
        except httpx.HTTPError as exc:
            raise ApiError(502, "ASR_PROVIDER_ERROR", "Speech service failed. Please try again or type your message.", "audio") from exc
        if response.status_code >= 500:
            raise ApiError(502, "ASR_PROVIDER_ERROR", "Speech service failed. Please try again or type your message.", "audio")
        if response.status_code >= 400:
            raise ApiError(415, "UNSUPPORTED_AUDIO_FORMAT", "This audio format is not supported. Please record again or type your message.", "audio")
        payload = response.json()
        transcript = (payload.get("text") or "").strip()
        detected_language = _normalize_language(payload.get("language"), language_hint)
        confidence = _confidence_from_verbose_json(payload, bool(transcript))
        duration_ms = int(float(payload.get("duration") or 0) * 1000)
        return AsrResponseModel(
            transcript=transcript,
            detected_language_code=detected_language,
            confidence=confidence,
            duration_ms=duration_ms,
            provider="groq",
            confidence_method="verbose_json" if "segments" in payload else "provider_default",
        )


def _confidence_from_verbose_json(payload: dict, has_transcript: bool) -> float:
    segments = payload.get("segments") or []
    probs = [segment.get("avg_logprob") for segment in segments if segment.get("avg_logprob") is not None]
    if probs:
        avg = sum(float(item) for item in probs) / len(probs)
        return max(0.0, min(1.0, 1.0 + avg))
    return 0.85 if has_transcript else 0.0


def _normalize_language(value: str | None, fallback: str | None) -> str:
    code = (value or fallback or "en").lower()
    aliases = {"english": "en", "hindi": "hi", "odia": "or"}
    return aliases.get(code, code[:2])
