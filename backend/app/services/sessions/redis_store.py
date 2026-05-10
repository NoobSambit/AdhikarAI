import json
from datetime import datetime, timezone
from typing import Any

SESSION_KEY_VERSION = "phase2.langgraph.v1"


class RedisSessionStore:
    _memory: dict[str, tuple[dict[str, Any], int]] = {}

    def __init__(self, redis_url: str, ttl_seconds: int) -> None:
        self.redis_url = redis_url
        self.ttl_seconds = ttl_seconds
        self._client = None

    async def _redis(self):
        if self.redis_url.startswith("memory://"):
            return None
        if self._client is None:
            try:
                from redis.asyncio import from_url
            except Exception as exc:  # pragma: no cover
                raise RuntimeError("redis package is required for Redis-backed sessions") from exc
            self._client = from_url(self.redis_url, decode_responses=True)
        return self._client

    async def write_state(self, key: str, state: dict[str, Any]) -> None:
        payload = {"state": state, "updated_at": datetime.now(timezone.utc).isoformat(), "version": SESSION_KEY_VERSION}
        if self.redis_url.startswith("memory://"):
            self._memory[key] = (payload, self.ttl_seconds)
            return
        client = await self._redis()
        await client.set(key, json.dumps(payload), ex=self.ttl_seconds)

    async def read_state(self, key: str) -> dict[str, Any] | None:
        if self.redis_url.startswith("memory://"):
            stored = self._memory.get(key)
            return stored[0] if stored else None
        client = await self._redis()
        raw = await client.get(key)
        return json.loads(raw) if raw else None

    async def ttl(self, key: str) -> int:
        if self.redis_url.startswith("memory://"):
            stored = self._memory.get(key)
            return stored[1] if stored else -2
        client = await self._redis()
        return int(await client.ttl(key))


def session_redis_key(organisation_id: str, session_id: str) -> str:
    return f"session:{organisation_id}:{session_id}"
