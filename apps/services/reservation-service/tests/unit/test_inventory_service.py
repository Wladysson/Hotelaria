from unittest.mock import AsyncMock

import pytest

from src.services.inventory_service import InventoryService


@pytest.fixture
def reservation_repository():
    return AsyncMock()


@pytest.fixture
def inventory_service(reservation_repository):
    return InventoryService(
        reservation_repository=reservation_repository,
    )


@pytest.mark.asyncio
async def test_service_must_be_created(
    inventory_service,
):
    assert inventory_service is not None


@pytest.mark.asyncio
async def test_service_must_have_reservation_repository(
    inventory_service,
    reservation_repository,
):
    assert (
        inventory_service.reservation_repository
        is reservation_repository
    )