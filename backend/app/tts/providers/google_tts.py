import base64
import httpx

from app.core.config import Settings
from app.core.errors import ApiError
from app.schemas.tts import TtsRequestModel


class GoogleTTSProvider:
    provider = "google"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def synthesize(self, request: TtsRequestModel, voice_name: str) -> tuple[bytes, str]:
        if not self.settings.google_application_credentials and not self.settings.google_translate_api_key:
            raise ApiError(502, "TTS_PROVIDER_ERROR", "Voice playback failed. You can read the text or try again.", None)
        payload = {
            "input": {"text": request.text},
            "voice": {"languageCode": voice_name.split("-Wavenet")[0].split("-Standard")[0], "name": voice_name},
            "audioConfig": {"audioEncoding": "MP3", "speakingRate": request.speaking_rate},
        }
        params = {"key": self.settings.google_translate_api_key} if self.settings.google_translate_api_key else None
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.post(self.settings.google_tts_url, params=params, json=payload)
        except httpx.HTTPError as exc:
            raise ApiError(502, "TTS_PROVIDER_ERROR", "Voice playback failed. You can read the text or try again.", None) from exc
        if response.status_code >= 400:
            raise ApiError(502, "TTS_PROVIDER_ERROR", "Voice playback failed. You can read the text or try again.", None)
        audio = base64.b64decode(response.json().get("audioContent", ""))
        return audio, "audio/mpeg"
