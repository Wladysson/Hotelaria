from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.reservation import Reservation, ReservationStatus


class ReservationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        reservation: Reservation,
    ) -> Reservation:
        self.session.add(reservation)
        await self.session.flush()
        await self.session.refresh(reservation)

        return reservation

    async def get_by_id(
        self,
        reservation_id: UUID,
    ) -> Reservation | None:
        statement = (
            select(Reservation)
            .where(Reservation.id == reservation_id)
            .options(
                selectinload(Reservation.items),
                selectinload(Reservation.primary_guest),
                selectinload(Reservation.cancellation_policy),
                selectinload(Reservation.holds),
            )
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_by_code(
        self,
        reservation_code: str,
    ) -> Reservation | None:
        statement = (
            select(Reservation)
            .where(
                Reservation.reservation_code == reservation_code
            )
            .options(
                selectinload(Reservation.items),
                selectinload(Reservation.primary_guest),
                selectinload(Reservation.cancellation_policy),
                selectinload(Reservation.holds),
            )
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> Reservation | None:
        statement = select(Reservation).where(
            Reservation.idempotency_key == idempotency_key
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Reservation], int]:
        offset = (page - 1) * page_size

        count_statement = (
            select(func.count())
            .select_from(Reservation)
            .where(Reservation.user_id == user_id)
        )

        total = await self.session.scalar(count_statement) or 0

        statement = (
            select(Reservation)
            .where(Reservation.user_id == user_id)
            .order_by(Reservation.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .options(
                selectinload(Reservation.items),
                selectinload(Reservation.primary_guest),
            )
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all()), total

    async def get_by_hotel(
        self,
        hotel_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Reservation], int]:
        offset = (page - 1) * page_size

        count_statement = (
            select(func.count())
            .select_from(Reservation)
            .where(Reservation.hotel_id == hotel_id)
        )

        total = await self.session.scalar(count_statement) or 0

        statement = (
            select(Reservation)
            .where(Reservation.hotel_id == hotel_id)
            .order_by(Reservation.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .options(
                selectinload(Reservation.items),
                selectinload(Reservation.primary_guest),
            )
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all()), total

    async def find_active_by_room(
        self,
        room_id: UUID,
        check_in: date,
        check_out: date,
    ) -> list[Reservation]:
        statement = (
            select(Reservation)
            .join(Reservation.items)
            .where(
                Reservation.items.any(
                    (lambda item: item.room_id == room_id)
                )
            )
        )

        statement = statement.where(
            Reservation.status.in_(
                [
                    ReservationStatus.PENDING,
                    ReservationStatus.PAYMENT_PENDING,
                    ReservationStatus.CONFIRMED,
                ]
            )
        )

        result = await self.session.execute(statement)

        return list(result.scalars().unique().all())

    async def update(
        self,
        reservation: Reservation,
    ) -> Reservation:
        self.session.add(reservation)
        await self.session.flush()
        await self.session.refresh(reservation)

        return reservation

    async def update_status(
        self,
        reservation: Reservation,
        status: ReservationStatus,
    ) -> Reservation:
        reservation.status = status

        self.session.add(reservation)
        await self.session.flush()
        await self.session.refresh(reservation)

        return reservation

    async def delete(
        self,
        reservation: Reservation,
    ) -> None:
        await self.session.delete(reservation)
        await self.session.flush()