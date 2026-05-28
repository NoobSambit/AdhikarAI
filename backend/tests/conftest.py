import os
from collections.abc import AsyncIterator
from uuid import uuid4

import pytest_asyncio
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.db.base import Base
from app.db.models import Organisation

os.environ.setdefault("ENABLE_SCHEDULER", "false")
os.environ.setdefault("REDIS_URL", "memory://")


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    settings = get_settings()
    database_url = settings.test_database_url or settings.database_url
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        try:
            yield session
        finally:
            await session.close()
    await engine.dispose()


@pytest_asyncio.fixture
async def organisation(db_session: AsyncSession) -> Organisation:
    org = Organisation(id=uuid4(), slug=f"test-{uuid4().hex}", name="Test NGO", organisation_type="ngo")
    db_session.add(org)
    await db_session.commit()
    return org
