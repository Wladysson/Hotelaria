import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.database import get_db
from src.main import app
from src.models.base import Base


TEST_DATABASE_URL = (
    "sqlite+aiosqlite:///:memory:"
)


engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
)

TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(
    scope="session"
)
def event_loop():
    loop = asyncio.new_event_loop()

    yield loop

    loop.close()


@pytest_asyncio.fixture(
    scope="session",
    autouse=True,
)
async def setup_database():
    async with engine.begin() as connection:
        await connection.run_sync(
            Base.metadata.create_all
        )

    yield

    async with engine.begin() as connection:
        await connection.run_sync(
            Base.metadata.drop_all
        )

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[
    AsyncSession,
    None,
]:
    async with TestingSessionLocal() as session:
        try:
            yield session

            await session.rollback()

        except Exception:
            await session.rollback()

            raise

        finally:
            await session.close()


@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession,
) -> AsyncGenerator[
    AsyncClient,
    None,
]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[
        get_db
    ] = override_get_db

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as async_client:
        yield async_client

    app.dependency_overrides.clear()