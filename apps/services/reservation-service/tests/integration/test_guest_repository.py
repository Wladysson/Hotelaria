import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.guest_repository import GuestRepository


@pytest.mark.asyncio
async def test_guest_repository_can_be_created(
    db_session: AsyncSession,
):
    repository = GuestRepository(db_session)

    assert repository is not None
    assert repository.session is db_session


@pytest.mark.asyncio
async def test_guest_repository_uses_database_session(
    db_session: AsyncSession,
):
    repository = GuestRepository(db_session)

    assert repository.session is not None
    assert isinstance(repository.session, AsyncSession)