import httpx

from app.core.config import Settings
from app.core.errors import ApiError
from app.schemas.translation import TranslateRequestModel, TranslateResponseModel


class AI4BharatHostedProvider:
    provider = "ai4bharat_hosted"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def translate(self, request: TranslateRequestModel) -> TranslateResponseModel:
        if not self.settings.ai4bharat_translate_url:
            raise ApiError(
                500,
                "TRANSLATION_PROVIDER_MISCONFIGURED",
                "AI4Bharat hosted translation URL is not configured.",
                "AI4BHARAT_TRANSLATE_URL",
            )
        headers = {"Authorization": f"Bearer {self.settings.ai4bharat_api_key}"} if self.settings.ai4bharat_api_key else {}
        try:
            async with httpx.AsyncClient(timeout=self.settings.ai4bharat_timeout_seconds) as client:
                response = await client.post(self.settings.ai4bharat_translate_url, headers=headers, json=request.model_dump(mode="json"))
        except httpx.HTTPError as exc:
            raise ApiError(502, "TRANSLATION_UNAVAILABLE", "Translation failed. You can read the text or type again.", None) from exc
        if response.status_code >= 400:
            raise ApiError(502, "TRANSLATION_UNAVAILABLE", "Translation failed. You can read the text or type again.", None)
        payload = response.json()
        return TranslateResponseModel(
            translated_text=payload.get("translated_text") or payload.get("translation") or request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            provider="ai4bharat_hosted",
            cached=False,
        )
