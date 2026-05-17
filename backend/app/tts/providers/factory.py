from app.core.config import get_settings
from app.core.errors import ApiError
from app.tts.client import TTSClient
from app.tts.providers.google_tts import GoogleTTSProvider
from app.tts.providers.local_indictts import LocalIndicTTSProvider


def get_tts_client() -> TTSClient:
    settings = get_settings()
    if settings.tts_provider == "local_indictts":
        provider = LocalIndicTTSProvider(settings)
    elif settings.tts_provider == "google":
        provider = GoogleTTSProvider(settings)
    else:
        raise ApiError(500, "TTS_PROVIDER_MISCONFIGURED", "TTS provider is not configured.", "TTS_PROVIDER")
    return TTSClient(provider, redis_url=settings.redis_url, ttl_seconds=settings.tts_cache_ttl_seconds)
