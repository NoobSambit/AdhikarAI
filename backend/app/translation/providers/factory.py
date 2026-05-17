from app.core.config import get_settings
from app.core.errors import ApiError
from app.translation.client import TranslationClient
from app.translation.providers.ai4bharat_hosted import AI4BharatHostedProvider
from app.translation.providers.google_translate import GoogleTranslateProvider
from app.translation.providers.local_indictrans2 import LocalIndicTrans2Provider


def get_translation_client() -> TranslationClient:
    settings = get_settings()
    if settings.translation_provider == "local_indictrans2":
        provider = LocalIndicTrans2Provider(settings)
    elif settings.translation_provider == "ai4bharat_hosted":
        provider = AI4BharatHostedProvider(settings)
    elif settings.translation_provider == "google":
        provider = GoogleTranslateProvider(settings)
    else:
        raise ApiError(500, "TRANSLATION_PROVIDER_MISCONFIGURED", "Translation provider is not configured.", "TRANSLATION_PROVIDER")
    fallback = GoogleTranslateProvider(settings) if settings.google_translate_api_key and settings.translation_provider != "google" else None
    return TranslationClient(provider, fallback=fallback, redis_url=settings.redis_url, ttl_seconds=settings.translation_cache_ttl_seconds)
