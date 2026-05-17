from uuid import UUID

import pytest

from app.core.errors import ApiError
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
