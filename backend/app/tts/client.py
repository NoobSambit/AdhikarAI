import base64
import json
import time
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import TTSEvent
from app.schemas.tts import TtsRequestModel, TtsResponseModel
from app.services.sessions.redis_store import RedisSessionStore
from app.tts.cache import tts_cache_key
from app.tts.providers.base import TTSProviderClient
from app.tts.voices import voice_name_for_language


class TTSClient:
    _memory_cache: dict[str, dict[str, Any]] = {}

    def __init__(self, provider: TTSProviderClient, redis_url: str, ttl_seconds: int) -> None:
        self.provider = provider
        self.store = RedisSessionStore(redis_url, ttl_seconds)
        self.ttl_seconds = ttl_seconds

    async def synthesize_to_url(
        self,
        request: TtsRequestModel,
        db: AsyncSession | None = None,
        organisation_id: UUID | None = None,
        conversation_session_id: UUID | None = None,
    ) -> TtsResponseModel:
        voice_name = voice_name_for_language(request.language_code, self.provider.provider)
        key = tts_cache_key(request.text, request.language_code, voice_name, request.speaking_rate)
        cached = await self.get_audio(key)
        if cached:
            await self._persist_event(db, organisation_id, conversation_session_id, request, voice_name, key, cached["mime_type"], len(cached["audio"]), "cache_hit", 0, None)
            return TtsResponseModel(audio_url=f"/voice/tts/audio/{key}", audio_mime_type=cached["mime_type"], provider=self.provider.provider, cached=True)
        started = time.monotonic()
        audio, mime_type = await self.provider.synthesize(request, voice_name)
        await self._cache_set(key, audio, mime_type)
        await self._persist_event(db, organisation_id, conversation_session_id, request, voice_name, key, mime_type, len(audio), "success", int((time.monotonic() - started) * 1000), None)
        return TtsResponseModel(audio_url=f"/voice/tts/audio/{key}", audio_mime_type=mime_type, provider=self.provider.provider, cached=False)

    async def get_audio(self, key: str) -> dict[str, Any] | None:
        if self.store.redis_url.startswith("memory://"):
            return self._memory_cache.get(key)
        raw = await (await self.store._redis()).get(key)
        if not raw:
            return None
        payload = json.loads(raw)
        return {"audio": base64.b64decode(payload["audio"]), "mime_type": payload["mime_type"]}

    async def _cache_set(self, key: str, audio: bytes, mime_type: str) -> None:
        if self.store.redis_url.startswith("memory://"):
            self._memory_cache[key] = {"audio": audio, "mime_type": mime_type}
            return
        payload = {"audio": base64.b64encode(audio).decode("ascii"), "mime_type": mime_type}
        await (await self.store._redis()).set(key, json.dumps(payload), ex=self.ttl_seconds)

    async def _persist_event(
        self,
        db: AsyncSession | None,
        organisation_id: UUID | None,
        conversation_session_id: UUID | None,
        request: TtsRequestModel,
        voice_name: str,
        key: str,
        mime_type: str,
        size: int,
        status: str,
        latency_ms: int,
        error_code: str | None,
    ) -> None:
        if db is None or organisation_id is None:
            return
        db.add(
            TTSEvent(
                organisation_id=organisation_id,
                conversation_session_id=conversation_session_id,
                provider=self.provider.provider,
                language_code=request.language_code,
                voice_name=voice_name,
                text_hash=key,
                audio_mime_type=mime_type,
                audio_size_bytes=size,
                speaking_rate=request.speaking_rate,
                status=status,
                latency_ms=latency_ms,
                error_code=error_code,
            )
        )
