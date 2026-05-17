import httpx

from app.core.config import Settings
from app.core.errors import ApiError
from app.schemas.translation import TranslateRequestModel, TranslateResponseModel


class LocalIndicTrans2Provider:
    provider = "local_indictrans2"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def translate(self, request: TranslateRequestModel) -> TranslateResponseModel:
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                response = await client.post(
                    f"{self.settings.translation_service_url.rstrip('/')}/translate",
                    json=request.model_dump(mode="json"),
                )
        except httpx.HTTPError as exc:
            raise ApiError(502, "TRANSLATION_UNAVAILABLE", "Translation failed. You can read the text or type again.", None) from exc
        if response.status_code >= 400:
            raise ApiError(502, "TRANSLATION_UNAVAILABLE", "Translation failed. You can read the text or type again.", None)
        payload = response.json()
        return TranslateResponseModel(
            translated_text=payload.get("translated_text", request.text),
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            provider="local_indictrans2",
            cached=False,
        )
