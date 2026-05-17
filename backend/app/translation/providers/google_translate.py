import httpx

from app.core.config import Settings
from app.core.errors import ApiError
from app.schemas.translation import TranslateRequestModel, TranslateResponseModel


class GoogleTranslateProvider:
    provider = "google"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def translate(self, request: TranslateRequestModel) -> TranslateResponseModel:
        if not self.settings.google_translate_api_key:
            raise ApiError(502, "TRANSLATION_UNAVAILABLE", "Translation is unavailable. Please read the text or type again.", None)
        params = {"key": self.settings.google_translate_api_key}
        payload = {"q": request.text, "source": request.source_lang, "target": request.target_lang, "format": "text"}
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                response = await client.post(self.settings.google_translate_url, params=params, data=payload)
        except httpx.HTTPError as exc:
            raise ApiError(502, "TRANSLATION_UNAVAILABLE", "Translation failed. You can read the text or type again.", None) from exc
        if response.status_code >= 400:
            raise ApiError(502, "TRANSLATION_UNAVAILABLE", "Translation failed. You can read the text or type again.", None)
        data = response.json().get("data", {})
        translated = (data.get("translations") or [{}])[0].get("translatedText", request.text)
        return TranslateResponseModel(
            translated_text=translated,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            provider="google",
            cached=False,
        )
