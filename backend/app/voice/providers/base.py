from typing import Protocol

from app.schemas.voice import AsrResponseModel


class ASRProvider(Protocol):
    async def transcribe(self, audio: bytes, mime_type: str, language_hint: str | None) -> AsrResponseModel: ...
