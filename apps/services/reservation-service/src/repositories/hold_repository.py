from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.hold import Hold, HoldStatus


class HoldRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        hold: Hold,
    ) -> Hold:
        self.session.add(hold)
        await self.session.flush()
        await self.session.refresh(hold)

        return hold

    async def get_by_id(
        self,
        hold_id: UUID,
    ) -> Hold | None:
        statement = select(Hold).where(
            Hold.id == hold_id
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> Hold | None:
        statement = select(Hold).where(
            Hold.idempotency_key == idempotency_key
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_active_by_room(
        self,
        room_id: UUID,
        check_in: date,
        check_out: date,
    ) -> list[Hold]:
        statement = (
            select(Hold)
            .where(
                Hold.room_id == room_id,
                Hold.status == HoldStatus.ACTIVE,
                Hold.check_in < datetime.combine(
                    check_out,
                    datetime.min.time(),
                ),
                Hold.check_out > datetime.combine(
                    check_in,
                    datetime.min.time(),
                ),
            )
            .order_by(Hold.created_at.asc())
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all())

    async def get_active_by_reservation(
        self,
        reservation_id: UUID,
    ) -> list[Hold]:
        statement = (
            select(Hold)
            .where(
                Hold.reservation_id == reservation_id,
                Hold.status == HoldStatus.ACTIVE,
            )
            .order_by(Hold.created_at.asc())
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all())

    async def get_expired(
        self,
        now: datetime,
        limit: int = 100,
    ) -> list[Hold]:
        statement = (
            select(Hold)
            .where(
                Hold.status == HoldStatus.ACTIVE,
                Hold.expires_at <= now,
            )
            .order_by(Hold.expires_at.asc())
            .limit(limit)
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all())

    async def update_status(
        self,
        hold: Hold,
        status: HoldStatus,
    ) -> Hold:
        hold.status = status

        self.session.add(hold)
        await self.session.flush()
        await self.session.refresh(hold)

        return hold

    async def release(
        self,
        hold: Hold,
    ) -> Hold:
        hold.status = HoldStatus.RELEASED

        self.session.add(hold)
        await self.session.flush()
        await self.session.refresh(hold)

        return hold

    async def confirm(
        self,
        hold: Hold,
    ) -> Hold:
        hold.status = HoldStatus.CONFIRMED

        self.session.add(hold)
        await self.session.flush()
        await self.session.refresh(hold)

        return hold