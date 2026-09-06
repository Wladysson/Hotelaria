from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.services.reservation_service import ReservationService


@pytest.fixture
def reservation_repository():
    return AsyncMock()


@pytest.fixture
def hold_repository():
    return AsyncMock()


@pytest.fixture
def guest_repository():
    return AsyncMock()


@pytest.fixture
def reservation_service(
    reservation_repository,
    hold_repository,
    guest_repository,
):
    return ReservationService(
        reservation_repository=reservation_repository,
        hold_repository=hold_repository,
        guest_repository=guest_repository,
    )


@pytest.mark.asyncio
async def test_service_must_be_created(
    reservation_service,
):
    assert reservation_service is not None


@pytest.mark.asyncio
async def test_create_reservation_must_call_repository(
    reservation_service,
    reservation_repository,
):
    reservation_id = uuid4()

    reservation_repository.create.return_value = MagicMock(
        id=reservation_id
    )

    assert hasattr(reservation_service, "reservation_repository")
    assert (
        reservation_service.reservation_repository
        is reservation_repository
    )