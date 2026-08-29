from datetime import date
from uuid import UUID

from src.core.exceptions import ReservationConflictError
from src.repositories.reservation_repository import ReservationRepository


class InventoryService:
    """
    Serviço responsável pelo controle lógico do inventário
    de quartos durante o ciclo da reserva.
    """

    def __init__(
        self,
        reservation_repository: ReservationRepository,
    ) -> None:
        self.reservation_repository = reservation_repository

    async def reserve_inventory(
        self,
        hotel_id: UUID,
        check_in: date,
        check_out: date,
        rooms: int,
    ) -> bool:
        """
        Reserva unidades do inventário para o período solicitado.
        """

        if check_out <= check_in:
            return False

        if rooms < 1:
            return False

        available = await self.reservation_repository.check_room_inventory(
            hotel_id=hotel_id,
            check_in=check_in,
            check_out=check_out,
            rooms=rooms,
        )

        if not available:
            raise ReservationConflictError(
                "Inventário insuficiente para a reserva."
            )

        return await self.reservation_repository.reserve_inventory(
            hotel_id=hotel_id,
            check_in=check_in,
            check_out=check_out,
            rooms=rooms,
        )

    async def release_inventory(
        self,
        hotel_id: UUID,
        check_in: date,
        check_out: date,
        rooms: int,
    ) -> bool:
        """
        Libera unidades de inventário após cancelamento.
        """

        if check_out <= check_in:
            return False

        if rooms < 1:
            return False

        return await self.reservation_repository.release_inventory(
            hotel_id=hotel_id,
            check_in=check_in,
            check_out=check_out,
            rooms=rooms,
        )

    async def get_inventory(
        self,
        hotel_id: UUID,
        check_in: date,
        check_out: date,
    ):
        """
        Consulta o inventário disponível.
        """

        if check_out <= check_in:
            return []

        return await self.reservation_repository.get_inventory(
            hotel_id=hotel_id,
            check_in=check_in,
            check_out=check_out,
        )