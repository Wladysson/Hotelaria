from datetime import date
from decimal import Decimal
from uuid import UUID

from src.core.exceptions import (
    ReservationConflictError,
    ReservationNotFoundError,
)
from src.repositories.reservation_repository import ReservationRepository
from src.repositories.guest_repository import GuestRepository
from src.repositories.hold_repository import HoldRepository
from src.services.inventory_service import InventoryService
from src.services.availability_service import AvailabilityService


class ReservationService:
    """
    Serviço responsável pelo ciclo de vida das reservas.

    Coordena:
    - criação de reservas;
    - consulta;
    - atualização;
    - cancelamento;
    - hóspedes;
    - disponibilidade;
    - reservas de estoque;
    - holds financeiros.
    """

    def __init__(
        self,
        reservation_repository: ReservationRepository,
        guest_repository: GuestRepository,
        hold_repository: HoldRepository,
        availability_service: AvailabilityService,
        inventory_service: InventoryService,
    ) -> None:
        self.reservation_repository = reservation_repository
        self.guest_repository = guest_repository
        self.hold_repository = hold_repository
        self.availability_service = availability_service
        self.inventory_service = inventory_service

    async def create_reservation(
        self,
        user_id: UUID,
        hotel_id: UUID,
        check_in: date,
        check_out: date,
        guests: int,
        rooms: int,
        total_amount: Decimal,
        guest_data: dict,
        items: list[dict],
    ):
        """
        Cria uma nova reserva após validar disponibilidade.
        """

        available = await self.availability_service.check_availability(
            hotel_id=hotel_id,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            rooms=rooms,
        )

        if not available:
            raise ReservationConflictError(
                "Não há disponibilidade para os parâmetros informados."
            )

        inventory_reserved = (
            await self.inventory_service.reserve_inventory(
                hotel_id=hotel_id,
                check_in=check_in,
                check_out=check_out,
                rooms=rooms,
            )
        )

        if not inventory_reserved:
            raise ReservationConflictError(
                "Não foi possível reservar o inventário."
            )

        guest = await self.guest_repository.create(
            user_id=user_id,
            data=guest_data,
        )

        reservation = await self.reservation_repository.create(
            user_id=user_id,
            hotel_id=hotel_id,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            rooms=rooms,
            total_amount=total_amount,
            guest_id=guest.id,
            items=items,
        )

        return reservation

    async def get_reservation(
        self,
        reservation_id: UUID,
        user_id: UUID | None = None,
    ):
        """
        Recupera uma reserva pelo identificador.
        """

        reservation = await self.reservation_repository.get_by_id(
            reservation_id
        )

        if reservation is None:
            raise ReservationNotFoundError(
                f"Reserva {reservation_id} não encontrada."
            )

        if user_id is not None and reservation.user_id != user_id:
            raise ReservationNotFoundError(
                f"Reserva {reservation_id} não encontrada."
            )

        return reservation

    async def list_reservations(
        self,
        user_id: UUID | None = None,
        hotel_id: UUID | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ):
        """
        Lista reservas com filtros e paginação.
        """

        return await self.reservation_repository.list(
            user_id=user_id,
            hotel_id=hotel_id,
            status=status,
            page=page,
            page_size=page_size,
        )

    async def update_reservation(
        self,
        reservation_id: UUID,
        user_id: UUID,
        data: dict,
    ):
        """
        Atualiza dados permitidos de uma reserva existente.
        """

        reservation = await self.get_reservation(
            reservation_id=reservation_id,
            user_id=user_id,
        )

        return await self.reservation_repository.update(
            reservation,
            data,
        )

    async def cancel_reservation(
        self,
        reservation_id: UUID,
        user_id: UUID,
        reason: str | None = None,
    ):
        """
        Cancela uma reserva e libera o inventário associado.
        """

        reservation = await self.get_reservation(
            reservation_id=reservation_id,
            user_id=user_id,
        )

        await self.inventory_service.release_inventory(
            hotel_id=reservation.hotel_id,
            check_in=reservation.check_in,
            check_out=reservation.check_out,
            rooms=reservation.rooms,
        )

        return await self.reservation_repository.cancel(
            reservation_id=reservation_id,
            reason=reason,
        )

    async def confirm_reservation(
        self,
        reservation_id: UUID,
        user_id: UUID,
    ):
        """
        Confirma uma reserva pendente.
        """

        reservation = await self.get_reservation(
            reservation_id=reservation_id,
            user_id=user_id,
        )

        return await self.reservation_repository.confirm(
            reservation.id
        )

    async def add_guest(
        self,
        reservation_id: UUID,
        user_id: UUID,
        guest_data: dict,
    ):
        """
        Adiciona um hóspede à reserva.
        """

        await self.get_reservation(
            reservation_id=reservation_id,
            user_id=user_id,
        )

        return await self.guest_repository.create(
            user_id=user_id,
            reservation_id=reservation_id,
            data=guest_data,
        )