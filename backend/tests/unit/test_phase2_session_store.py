import pytest

from app.services.sessions.redis_store import SESSION_KEY_VERSION, RedisSessionStore


@pytest.mark.asyncio
async def test_session_store_memory_ttl_resets_to_30_days():
    store = RedisSessionStore("memory://", ttl_seconds=2_592_000)
    key = "session:00000000-0000-0000-0000-000000000001:sess_test"

    await store.write_state(key, {"session_id": "sess_test"})
    ttl = await store.ttl(key)

    assert ttl == 2_592_000
    assert (await store.read_state(key))["version"] == SESSION_KEY_VERSION
