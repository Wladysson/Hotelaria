from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from src.services.saga.booking_saga import (
    BookingSaga,
    BookingSagaResult,
)
from src.services.saga.cancellation_saga import (
    CancellationSaga,
    CancellationSagaResult,
)


@dataclass
class BookingOperationResult:
    success: bool
    hotel_id: UUID
    rooms: int
    total_amount: Decimal
    inventory_reserved: bool


@dataclass
class CancellationOperationResult:
    success: bool
    reservation_id: UUID
    inventory_released: bool


class SagaOrchestrator:

    def __init__(
        self,
        booking_saga: BookingSaga,
        cancellation_saga: CancellationSaga,
    ) -> None:
        self.booking_saga = booking_saga
        self.cancellation_saga = cancellation_saga

    async def create_booking(
        self,
        hotel_id: UUID,
        check_in: date,
        check_out: date,
        guests: int,
        rooms: int,
        price_per_night: Decimal,
        discount_percent: Decimal = Decimal("0"),
        tax_percent: Decimal = Decimal("0"),
    ) -> BookingOperationResult:

        result: BookingSagaResult = (
            await self.booking_saga.execute(
                hotel_id=hotel_id,
                check_in=check_in,
                check_out=check_out,
                guests=guests,
                rooms=rooms,
                price_per_night=price_per_night,
                discount_percent=discount_percent,
                tax_percent=tax_percent,
            )
        )

        return BookingOperationResult(
            success=result.success,
            hotel_id=result.hotel_id,
            rooms=result.rooms,
            total_amount=result.total_amount,
            inventory_reserved=result.inventory_reserved,
        )

    async def cancel_booking(
        self,
        reservation_id: UUID,
        reason: str | None = None,
    ) -> CancellationOperationResult:

        result: CancellationSagaResult = (
            await self.cancellation_saga.execute(
                reservation_id=reservation_id,
                reason=reason,
            )
        )

        return CancellationOperationResult(
            success=result.success,
            reservation_id=result.reservation_id,
            inventory_released=result.inventory_released,
        )