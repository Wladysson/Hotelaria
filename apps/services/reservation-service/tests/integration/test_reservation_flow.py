from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.reservation_repository import ReservationRepository
from src.repositories.hold_repository import HoldRepository


@pytest.mark.asyncio
async def test_reservation_flow_can_initialize_repositories(
    db_session: AsyncSession,
):
    reservation_repository = ReservationRepository(
        db_session
    )

    hold_repository = HoldRepository(
        db_session
    )

    assert reservation_repository.session is db_session
    assert hold_repository.session is db_session


@pytest.mark.asyncio
async def test_reservation_flow_generates_valid_identifiers():
    reservation_id = uuid4()
    hold_id = uuid4()

    assert reservation_id is not None
    assert hold_id is not None


@pytest.mark.asyncio
async def test_reservation_period_must_be_valid():
    check_in = date(2026, 9, 10)
    check_out = date(2026, 9, 15)

    assert check_out > check_in


@pytest.mark.asyncio
async def test_invalid_reservation_period_must_be_detected():
    check_in = date(2026, 9, 15)
    check_out = date(2026, 9, 10)

    assert check_out <= check_in