from decimal import Decimal
from uuid import UUID

from src.models.room import Room
from src.repositories.hotel_repository import HotelRepository
from src.repositories.room_repository import RoomRepository


class RoomService:

    def __init__(
        self,
        room_repository: RoomRepository,
        hotel_repository: HotelRepository,
    ):
        self.room_repository = room_repository
        self.hotel_repository = hotel_repository

    async def create_room(
        self,
        hotel_id: UUID,
        room_type_id: UUID,
        number: str,
        floor: int,
        price_per_night: Decimal,
        capacity: int,
        description: str | None = None,
    ) -> Room:
        hotel = await self.hotel_repository.get_by_id(hotel_id)

        if hotel is None:
            raise ValueError("Hotel não encontrado")

        if not hotel.is_active:
            raise ValueError(
                "Não é possível adicionar quartos a um hotel inativo"
            )

        if floor < 0:
            raise ValueError(
                "O andar do quarto não pode ser negativo"
            )

        if capacity < 1:
            raise ValueError(
                "A capacidade do quarto deve ser maior que zero"
            )

        if price_per_night <= Decimal("0"):
            raise ValueError(
                "O preço da diária deve ser maior que zero"
            )

        normalized_number = number.strip()

        if not normalized_number:
            raise ValueError(
                "O número do quarto não pode ser vazio"
            )

        existing_room = await self.room_repository.get_by_number(
            hotel_id=hotel_id,
            number=normalized_number,
        )

        if existing_room is not None:
            raise ValueError(
                "Já existe um quarto com este número neste hotel"
            )

        room = Room(
            hotel_id=hotel_id,
            room_type_id=room_type_id,
            number=normalized_number,
            floor=floor,
            price_per_night=price_per_night,
            capacity=capacity,
            description=description,
            is_active=True,
        )

        return await self.room_repository.create(room)

    async def get_room(
        self,
        room_id: UUID,
    ) -> Room:
        room = await self.room_repository.get_by_id(room_id)

        if room is None:
            raise ValueError("Quarto não encontrado")

        return room

    async def get_room_with_details(
        self,
        room_id: UUID,
    ) -> Room:
        room = await self.room_repository.get_by_id_with_details(
            room_id
        )

        if room is None:
            raise ValueError("Quarto não encontrado")

        return room

    async def list_rooms(
        self,
        hotel_id: UUID,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Room]:
        hotel = await self.hotel_repository.get_by_id(hotel_id)

        if hotel is None:
            raise ValueError("Hotel não encontrado")

        if skip < 0:
            skip = 0

        if limit < 1:
            raise ValueError("O limite deve ser maior que zero")

        if limit > 100:
            limit = 100

        return await self.room_repository.list_by_hotel(
            hotel_id=hotel_id,
            active_only=active_only,
            skip=skip,
            limit=limit,
        )

    async def update_room(
        self,
        room_id: UUID,
        room_type_id: UUID | None = None,
        number: str | None = None,
        floor: int | None = None,
        price_per_night: Decimal | None = None,
        capacity: int | None = None,
        description: str | None = None,
    ) -> Room:
        room = await self.room_repository.get_by_id(room_id)

        if room is None:
            raise ValueError("Quarto não encontrado")

        if number is not None:
            normalized_number = number.strip()

            if not normalized_number:
                raise ValueError(
                    "O número do quarto não pode ser vazio"
                )

            if normalized_number != room.number:
                existing_room = (
                    await self.room_repository.get_by_number(
                        hotel_id=room.hotel_id,
                        number=normalized_number,
                    )
                )

                if (
                    existing_room is not None
                    and existing_room.id != room.id
                ):
                    raise ValueError(
                        "Já existe um quarto com este número neste hotel"
                    )

            room.number = normalized_number

        if room_type_id is not None:
            room.room_type_id = room_type_id

        if floor is not None:
            if floor < 0:
                raise ValueError(
                    "O andar do quarto não pode ser negativo"
                )

            room.floor = floor

        if price_per_night is not None:
            if price_per_night <= Decimal("0"):
                raise ValueError(
                    "O preço da diária deve ser maior que zero"
                )

            room.price_per_night = price_per_night

        if capacity is not None:
            if capacity < 1:
                raise ValueError(
                    "A capacidade do quarto deve ser maior que zero"
                )

            room.capacity = capacity

        if description is not None:
            room.description = description

        return await self.room_repository.update(room)

    async def activate_room(
        self,
        room_id: UUID,
    ) -> Room:
        room = await self.room_repository.get_by_id(room_id)

        if room is None:
            raise ValueError("Quarto não encontrado")

        hotel = await self.hotel_repository.get_by_id(room.hotel_id)

        if hotel is None:
            raise ValueError("Hotel associado ao quarto não encontrado")

        if not hotel.is_active:
            raise ValueError(
                "Não é possível ativar um quarto de um hotel inativo"
            )

        room.is_active = True

        return await self.room_repository.update(room)

    async def deactivate_room(
        self,
        room_id: UUID,
    ) -> Room:
        room = await self.room_repository.get_by_id(room_id)

        if room is None:
            raise ValueError("Quarto não encontrado")

        room.is_active = False

        return await self.room_repository.update(room)

    async def delete_room(
        self,
        room_id: UUID,
    ) -> None:
        room = await self.room_repository.get_by_id(room_id)

        if room is None:
            raise ValueError("Quarto não encontrado")

        await self.room_repository.delete(room)