from datetime import date
from uuid import UUID

from src.repositories.room_repository import RoomRepository
from src.repositories.hotel_repository import HotelRepository


class AvailabilityService:

    def __init__(
        self,
        room_repository: RoomRepository,
        hotel_repository: HotelRepository,
    ):
        self.room_repository = room_repository
        self.hotel_repository = hotel_repository

    async def check_room_availability(
        self,
        room_id: UUID,
        check_in: date,
        check_out: date,
    ) -> bool:
        self._validate_dates(
            check_in=check_in,
            check_out=check_out,
        )

        room = await self.room_repository.get_by_id(room_id)

        if room is None:
            raise ValueError("Quarto não encontrado")

        if not room.is_active:
            return False

        hotel = await self.hotel_repository.get_by_id(
            room.hotel_id
        )

        if hotel is None:
            raise ValueError(
                "Hotel associado ao quarto não encontrado"
            )

        if not hotel.is_active:
            return False

        return await self.room_repository.is_available(
            room_id=room_id,
            check_in=check_in,
            check_out=check_out,
        )

    async def get_available_rooms(
        self,
        hotel_id: UUID,
        check_in: date,
        check_out: date,
        guests: int = 1,
    ):
        self._validate_dates(
            check_in=check_in,
            check_out=check_out,
        )

        if guests < 1:
            raise ValueError(
                "A quantidade de hóspedes deve ser maior que zero"
            )

        hotel = await self.hotel_repository.get_by_id(hotel_id)

        if hotel is None:
            raise ValueError("Hotel não encontrado")

        if not hotel.is_active:
            return []

        return await self.room_repository.get_available_rooms(
            hotel_id=hotel_id,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
        )

    async def check_hotel_availability(
        self,
        hotel_id: UUID,
        check_in: date,
        check_out: date,
        guests: int = 1,
    ) -> bool:
        available_rooms = await self.get_available_rooms(
            hotel_id=hotel_id,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
        )

        return len(available_rooms) > 0

    async def get_available_room_count(
        self,
        hotel_id: UUID,
        check_in: date,
        check_out: date,
        guests: int = 1,
    ) -> int:
        available_rooms = await self.get_available_rooms(
            hotel_id=hotel_id,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
        )

        return len(available_rooms)

    @staticmethod
    def _validate_dates(
        check_in: date,
        check_out: date,
    ) -> None:
        if check_in < date.today():
            raise ValueError(
                "A data de check-in não pode estar no passado"
            )

        if check_out <= check_in:
            raise ValueError(
                "A data de check-out deve ser posterior ao check-in"
            )