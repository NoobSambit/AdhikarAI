from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from app.core.config import get_settings
from app.core.errors import ApiError

_MEMORY_COUNTS: dict[str, int] = defaultdict(int)
_REDIS_CLIENT = None


def seconds_until_next_midnight() -> int:
    now = datetime.now(timezone.utc)
    tomorrow = datetime.combine(now.date() + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
    return int((tomorrow - now).total_seconds())


async def check_rate_limit(actor_type: str, actor_id: str, organisation_id: UUID, limit: int) -> None:
    key = f"rate:{organisation_id}:{actor_type}:{actor_id}:{date.today().isoformat()}"
    count = await _increment_counter(key)
    if count > limit:
        retry = seconds_until_next_midnight()
        raise ApiError(
            429,
            "RATE_LIMIT_EXCEEDED",
            "You have used today's limit. Please try tomorrow or visit a CSC.",
            None,
            {
                "retry_after_seconds": retry,
                "retry_at": (datetime.now(timezone.utc) + timedelta(seconds=retry)).isoformat(),
            },
        )


async def _increment_counter(key: str) -> int:
    settings = get_settings()
    if settings.redis_url.startswith("memory://"):
        _MEMORY_COUNTS[key] += 1
        return _MEMORY_COUNTS[key]

    client = await _redis_client(settings.redis_url)
    count = int(await client.incr(key))
    if count == 1:
        await client.expire(key, seconds_until_next_midnight())
    return count


async def _redis_client(redis_url: str):
    global _REDIS_CLIENT
    if _REDIS_CLIENT is None:
        from redis.asyncio import from_url

        _REDIS_CLIENT = from_url(redis_url, decode_responses=True)
    return _REDIS_CLIENT


async def check_guest_limit(organisation_id: UUID, session_id: str) -> None:
    await check_rate_limit("guest", session_id, organisation_id, get_settings().rate_limit_guest_per_day)


async def check_operator_limit(organisation_id: UUID, member_id: UUID, units: int = 1) -> None:
    for _ in range(units):
        await check_rate_limit("operator", str(member_id), organisation_id, get_settings().rate_limit_operator_per_day)
