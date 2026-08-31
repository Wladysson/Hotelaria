from unittest.mock import AsyncMock

import pytest

from src.services.availability_service import AvailabilityService


@pytest.fixture
def reservation_repository():
    return AsyncMock()


@pytest.fixture
def availability_service(reservation_repository):
    return AvailabilityService(
        reservation_repository=reservation_repository,
    )


@pytest.mark.asyncio
async def test_service_must_be_created(
    availability_service,
):
    assert availability_service is not None


@pytest.mark.asyncio
async def test_service_must_have_reservation_repository(
    availability_service,
    reservation_repository,
):
    assert (
        availability_service.reservation_repository
        is reservation_repository
    )