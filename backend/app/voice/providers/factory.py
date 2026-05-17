from app.core.config import get_settings
from app.core.errors import ApiError
from app.voice.providers.browser_asr import BrowserASRProvider
from app.voice.providers.groq_whisper import GroqWhisperProvider
from app.voice.providers.whisper_cpp import WhisperCppProvider


def get_asr_provider():
    settings = get_settings()
    if settings.voice_provider == "local":
        return WhisperCppProvider(settings)
    if settings.voice_provider == "groq":
        return GroqWhisperProvider(settings)
    if settings.voice_provider == "browser":
        return BrowserASRProvider()
    raise ApiError(500, "VOICE_PROVIDER_MISCONFIGURED", "Voice provider is not configured.", "VOICE_PROVIDER")
