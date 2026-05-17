from typing import Protocol

from app.schemas.translation import TranslateRequestModel, TranslateResponseModel


class TranslationProviderClient(Protocol):
    async def translate(self, request: TranslateRequestModel) -> TranslateResponseModel: ...
