from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_reservation_endpoint_exists(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/reservations",
        json={},
    )

    assert response.status_code != 404


@pytest.mark.asyncio
async def test_get_reservation_endpoint_exists(
    client: AsyncClient,
):
    reservation_id = uuid4()

    response = await client.get(
        f"/api/v1/reservations/{reservation_id}",
    )

    assert response.status_code != 404


@pytest.mark.asyncio
async def test_list_reservations_endpoint_exists(
    client: AsyncClient,
):
    response = await client.get(
        "/api/v1/reservations",
    )

    assert response.status_code != 404