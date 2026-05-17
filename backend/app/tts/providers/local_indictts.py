import httpx

from app.core.config import Settings
from app.core.errors import ApiError
from app.schemas.tts import TtsRequestModel


class LocalIndicTTSProvider:
    provider = "local_indictts"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def synthesize(self, request: TtsRequestModel, voice_name: str) -> tuple[bytes, str]:
        try:
            async with httpx.AsyncClient(timeout=self.settings.local_tts_timeout_seconds) as client:
                response = await client.post(
                    f"{self.settings.local_tts_url.rstrip('/')}/synthesize",
                    json={
                        "text": request.text,
                        "language_code": request.language_code,
                        "speaker": "default_female",
                        "speaking_rate": request.speaking_rate,
                    },
                )
        except httpx.HTTPError as exc:
            raise ApiError(502, "TTS_PROVIDER_ERROR", "Voice playback failed. You can read the text or try again.", None) from exc
        if response.status_code >= 400:
            raise ApiError(502, "TTS_PROVIDER_ERROR", "Voice playback failed. You can read the text or try again.", None)
        return response.content, response.headers.get("content-type", "audio/wav").split(";")[0]
