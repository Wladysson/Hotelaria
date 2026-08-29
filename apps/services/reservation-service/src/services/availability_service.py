from datetime import date
from uuid import UUID

from src.repositories.reservation_repository import ReservationRepository


class AvailabilityService:
    """
    Serviço responsável pela validação de disponibilidade
    durante o período solicitado.
    """

    def __init__(
        self,
        reservation_repository: ReservationRepository,
    ) -> None:
        self.reservation_repository = reservation_repository

    async def check_availability(
        self,
        hotel_id: UUID,
        check_in: date,
        check_out: date,
        guests: int,
        rooms: int,
    ) -> bool:
        """
        Verifica se existe capacidade disponível para a reserva.
        """

        if check_out <= check_in:
            return False

        if guests < 1 or rooms < 1:
            return False

        return await self.reservation_repository.check_availability(
            hotel_id=hotel_id,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            rooms=rooms,
        )

    async def get_available_rooms(
        self,
        hotel_id: UUID,
        check_in: date,
        check_out: date,
        guests: int,
        rooms: int,
    ):
        """
        Retorna os quartos disponíveis para o período informado.
        """

        if check_out <= check_in:
            return []

        return await self.reservation_repository.get_available_rooms(
            hotel_id=hotel_id,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            rooms=rooms,
        )

    async def get_availability(
        self,
        hotel_id: UUID,
        check_in: date,
        check_out: date,
    ):
        """
        Retorna informações detalhadas de disponibilidade.
        """

        if check_out <= check_in:
            return []

        return await self.reservation_repository.get_availability(
            hotel_id=hotel_id,
            check_in=check_in,
            check_out=check_out,
        )