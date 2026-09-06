from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Cliente HTTP assíncrono para testes end-to-end.
    """

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client


@pytest_asyncio.fixture
async def authenticated_client(
    client: AsyncClient,
) -> AsyncClient:
    """
    Cliente HTTP autenticado para cenários protegidos.
    """

    client.headers.update(
        {
            "Authorization": "Bearer test-access-token",
        }
    )

    return client

