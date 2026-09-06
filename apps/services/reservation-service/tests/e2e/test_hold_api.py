from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_hold_endpoint_exists(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/holds",
        json={},
    )

    assert response.status_code != 404


@pytest.mark.asyncio
async def test_get_hold_endpoint_exists(
    client: AsyncClient,
):
    hold_id = uuid4()

    response = await client.get(
        f"/api/v1/holds/{hold_id}",
    )

    assert response.status_code != 404


@pytest.mark.asyncio
async def test_release_hold_endpoint_exists(
    client: AsyncClient,
):
    hold_id = uuid4()

    response = await client.delete(
        f"/api/v1/holds/{hold_id}",
    )

    assert response.status_code != 404