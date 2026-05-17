import json
import time
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.db.models import TranslationEvent
from app.schemas.translation import TranslateRequestModel, TranslateResponseModel
from app.services.sessions.redis_store import RedisSessionStore
from app.translation.cache import translation_cache_key
from app.translation.providers.base import TranslationProviderClient


class TranslationClient:
    _memory_cache: dict[str, str] = {}

    def __init__(
        self,
        provider: TranslationProviderClient,
        fallback: TranslationProviderClient | None,
        redis_url: str,
        ttl_seconds: int,
    ) -> None:
        self.provider = provider
        self.fallback = fallback
        self.store = RedisSessionStore(redis_url, ttl_seconds)
        self.ttl_seconds = ttl_seconds

    async def translate(
        self,
        request: TranslateRequestModel,
        db: AsyncSession | None = None,
        organisation_id: UUID | None = None,
        conversation_session_id: UUID | None = None,
    ) -> TranslateResponseModel:
        provider_name = getattr(self.provider, "provider", "local_indictrans2")
        if request.source_lang == request.target_lang:
            return TranslateResponseModel(
                translated_text=request.text,
                source_lang=request.source_lang,
                target_lang=request.target_lang,
                provider=provider_name,
                cached=True,
            )
        key = translation_cache_key(request.text, request.source_lang, request.target_lang, provider_name)
        cached = await self._cache_get(key)
        if cached:
            return TranslateResponseModel(
                translated_text=cached,
                source_lang=request.source_lang,
                target_lang=request.target_lang,
                provider=provider_name,
                cached=True,
            )
        started = time.monotonic()
        status = "success"
        error_code = None
        try:
            response = await self.provider.translate(request)
        except ApiError as exc:
            if not self.fallback:
                await self._persist_event(db, organisation_id, conversation_session_id, request, provider_name, None, "failed", int((time.monotonic() - started) * 1000), exc.code)
                return TranslateResponseModel(
                    translated_text=request.text,
                    source_lang=request.source_lang,
                    target_lang=request.target_lang,
                    provider=provider_name,
                    cached=False,
                    warning_code=exc.code,
                )
            response = await self.fallback.translate(request)
            status = "fallback_success"
            error_code = exc.code
        await self._cache_set(key, response.translated_text)
        await self._persist_event(db, organisation_id, conversation_session_id, request, response.provider, response.translated_text, status, int((time.monotonic() - started) * 1000), error_code)
        return response

    async def _cache_get(self, key: str) -> str | None:
        if self.store.redis_url.startswith("memory://"):
            return self._memory_cache.get(key)
        raw = await (await self.store._redis()).get(key)
        return json.loads(raw)["text"] if raw else None

    async def _cache_set(self, key: str, text: str) -> None:
        if self.store.redis_url.startswith("memory://"):
            self._memory_cache[key] = text
            return
        await (await self.store._redis()).set(key, json.dumps({"text": text}), ex=self.ttl_seconds)

    async def _persist_event(
        self,
        db: AsyncSession | None,
        organisation_id: UUID | None,
        conversation_session_id: UUID | None,
        request: TranslateRequestModel,
        provider: str,
        output: str | None,
        status: str,
        latency_ms: int,
        error_code: str | None,
    ) -> None:
        if db is None or organisation_id is None:
            return
        db.add(
            TranslationEvent(
                organisation_id=organisation_id,
                conversation_session_id=conversation_session_id,
                provider=provider,
                source_lang=request.source_lang,
                target_lang=request.target_lang,
                input_text_hash=translation_cache_key(request.text, request.source_lang, request.target_lang, provider),
                input_text_preview=request.text[:120],
                output_text_preview=output[:120] if output else None,
                status=status,
                latency_ms=latency_ms,
                error_code=error_code,
            )
        )
