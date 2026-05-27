from uuid import UUID

import pytest

from app.core.config import get_settings
from app.core.errors import ApiError
from app.rate_limit import service
from app.rate_limit.service import _MEMORY_COUNTS, check_rate_limit


ORG_ID = UUID("00000000-0000-0000-0000-000000000001")


@pytest.mark.asyncio
async def test_rate_limit_user_101st_request():
    _MEMORY_COUNTS.clear()

    for _ in range(100):
        await check_rate_limit("user", "user-1", ORG_ID, 100)

    with pytest.raises(ApiError) as exc:
        await check_rate_limit("user", "user-1", ORG_ID, 100)

    assert exc.value.code == "RATE_LIMIT_EXCEEDED"
    assert exc.value.details["retry_after_seconds"] > 0
    assert exc.value.details["retry_at"]


@pytest.mark.asyncio
async def test_rate_limit_uses_redis_counter_when_configured(monkeypatch):
    class FakeRedis:
        def __init__(self):
            self.counts: dict[str, int] = {}
            self.expirations: dict[str, int] = {}

        async def incr(self, key: str) -> int:
            self.counts[key] = self.counts.get(key, 0) + 1
            return self.counts[key]

        async def expire(self, key: str, seconds: int) -> None:
            self.expirations[key] = seconds

    fake = FakeRedis()
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    get_settings.cache_clear()
    monkeypatch.setattr(service, "_REDIS_CLIENT", fake)

    await check_rate_limit("operator", "member-1", ORG_ID, 2)
    await check_rate_limit("operator", "member-1", ORG_ID, 2)

    key = next(iter(fake.counts))
    assert key.startswith(f"rate:{ORG_ID}:operator:member-1:")
    assert fake.counts[key] == 2
    assert fake.expirations[key] > 0

    with pytest.raises(ApiError) as exc:
        await check_rate_limit("operator", "member-1", ORG_ID, 2)

    assert exc.value.code == "RATE_LIMIT_EXCEEDED"
    get_settings.cache_clear()


def test_memory_redis_rejected_in_deployed_env():
    from app.core.config import Settings

    with pytest.raises(ValueError):
        Settings(
            app_env="production",
            auth_jwt_secret="production-secret-with-more-than-32-chars",
            auth_cookie_secure=True,
            database_url="postgresql+asyncpg://prod:prod@db.example.test:5432/adhikarai",
            database_direct_url="postgresql+asyncpg://prod:prod@db.example.test:5432/adhikarai",
            redis_url="memory://",
            admin_api_token="prod-admin-token",
            otp_provider="msg91",
            msg91_auth_key="msg91-key",
            msg91_template_id="template",
            cors_origins="https://adhikarai.example.test",
        )
