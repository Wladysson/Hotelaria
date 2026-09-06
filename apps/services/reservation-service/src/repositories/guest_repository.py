from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.guest import Guest


class GuestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        guest: Guest,
    ) -> Guest:
        self.session.add(guest)
        await self.session.flush()
        await self.session.refresh(guest)

        return guest

    async def get_by_id(
        self,
        guest_id: UUID,
    ) -> Guest | None:
        statement = select(Guest).where(
            Guest.id == guest_id
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_by_user_id(
        self,
        user_id: UUID,
    ) -> list[Guest]:
        statement = (
            select(Guest)
            .where(
                Guest.user_id == user_id,
                Guest.is_active.is_(True),
            )
            .order_by(Guest.created_at.desc())
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all())

    async def get_by_email(
        self,
        email: str,
    ) -> Guest | None:
        statement = select(Guest).where(
            Guest.email == email
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_by_document(
        self,
        document_number: str,
    ) -> Guest | None:
        statement = select(Guest).where(
            Guest.document_number == document_number
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_primary_guest(
        self,
        user_id: UUID,
    ) -> Guest | None:
        statement = (
            select(Guest)
            .where(
                Guest.user_id == user_id,
                Guest.is_primary.is_(True),
                Guest.is_active.is_(True),
            )
            .limit(1)
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def update(
        self,
        guest: Guest,
    ) -> Guest:
        self.session.add(guest)
        await self.session.flush()
        await self.session.refresh(guest)

        return guest

    async def deactivate(
        self,
        guest: Guest,
    ) -> Guest:
        guest.is_active = False

        self.session.add(guest)
        await self.session.flush()
        await self.session.refresh(guest)

        return guest