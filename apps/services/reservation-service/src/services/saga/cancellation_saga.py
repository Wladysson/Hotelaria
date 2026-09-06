from dataclasses import dataclass
from uuid import UUID

from src.repositories.reservation_repository import ReservationRepository
from src.services.inventory_service import InventoryService


@dataclass
class CancellationSagaResult:
    success: bool
    reservation_id: UUID
    inventory_released: bool


class CancellationSaga:

    def __init__(
        self,
        reservation_repository: ReservationRepository,
        inventory_service: InventoryService,
    ) -> None:
        self.reservation_repository = reservation_repository
        self.inventory_service = inventory_service

    async def execute(
        self,
        reservation_id: UUID,
        reason: str | None = None,
    ) -> CancellationSagaResult:

        reservation = await self.reservation_repository.get_by_id(
            reservation_id
        )

        if reservation is None:
            return CancellationSagaResult(
                success=False,
                reservation_id=reservation_id,
                inventory_released=False,
            )

        inventory_released = (
            await self.inventory_service.release_inventory(
                hotel_id=reservation.hotel_id,
                check_in=reservation.check_in,
                check_out=reservation.check_out,
                rooms=reservation.rooms,
            )
        )

        if not inventory_released:
            return CancellationSagaResult(
                success=False,
                reservation_id=reservation_id,
                inventory_released=False,
            )

        await self.reservation_repository.cancel(
            reservation_id=reservation_id,
            reason=reason,
        )

        return CancellationSagaResult(
            success=True,
            reservation_id=reservation_id,
            inventory_released=True,
        )