from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cancel_reservation_endpoint_exists(
    client: AsyncClient,
):
    reservation_id = uuid4()

    response = await client.post(
        f"/api/v1/reservations/{reservation_id}/cancel",
    )

    assert response.status_code != 404


@pytest.mark.asyncio
async def test_get_cancellation_endpoint_exists(
    client: AsyncClient,
):
    reservation_id = uuid4()

    response = await client.get(
        f"/api/v1/reservations/{reservation_id}/cancellation",
    )

    assert response.status_code != 404