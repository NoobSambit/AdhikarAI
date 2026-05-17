from typing import Protocol

from app.schemas.tts import TtsRequestModel


class TTSProviderClient(Protocol):
    provider: str

    async def synthesize(self, request: TtsRequestModel, voice_name: str) -> tuple[bytes, str]: ...
