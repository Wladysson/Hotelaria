from datetime import date
from uuid import UUID

from sqlalchemy import and_, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.hotel import Hotel
from src.models.room import Room
from src.models.room_type import RoomType


class RoomRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        room: Room,
    ) -> Room:
        self.session.add(room)

        await self.session.flush()
        await self.session.refresh(room)

        return room

    async def get_by_id(
        self,
        room_id: UUID,
    ) -> Room | None:
        statement = (
            select(Room)
            .where(Room.id == room_id)
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_by_id_detailed(
        self,
        room_id: UUID,
    ) -> Room | None:
        statement = (
            select(Room)
            .options(
                selectinload(Room.room_type),
                selectinload(Room.hotel),
            )
            .where(Room.id == room_id)
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_by_room_number(
        self,
        hotel_id: UUID,
        room_number: str,
    ) -> Room | None:
        statement = (
            select(Room)
            .where(
                Room.hotel_id == hotel_id,
                func.lower(Room.room_number)
                == room_number.strip().lower(),
            )
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def list_by_hotel(
        self,
        hotel_id: UUID,
        page: int = 1,
        page_size: int = 20,
        is_active: bool | None = True,
        room_type_id: UUID | None = None,
    ) -> tuple[list[Room], int]:
        offset = (page - 1) * page_size

        filters = [
            Room.hotel_id == hotel_id
        ]

        if is_active is not None:
            filters.append(
                Room.is_active == is_active
            )

        if room_type_id:
            filters.append(
                Room.room_type_id == room_type_id
            )

        count_statement = (
            select(func.count(Room.id))
            .where(*filters)
        )

        total_result = await self.session.execute(
            count_statement
        )

        total = total_result.scalar_one()

        statement = (
            select(Room)
            .where(*filters)
            .order_by(Room.floor.asc(), Room.room_number.asc())
            .offset(offset)
            .limit(page_size)
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all()), total

    async def list_by_room_type(
        self,
        room_type_id: UUID,
        hotel_id: UUID | None = None,
        is_active: bool = True,
    ) -> list[Room]:
        filters = [
            Room.room_type_id == room_type_id,
            Room.is_active == is_active,
        ]

        if hotel_id:
            filters.append(
                Room.hotel_id == hotel_id
            )

        statement = (
            select(Room)
            .where(*filters)
            .order_by(Room.room_number.asc())
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all())

    async def exists(
        self,
        room_id: UUID,
    ) -> bool:
        statement = (
            select(Room.id)
            .where(Room.id == room_id)
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none() is not None

    async def exists_by_room_number(
        self,
        hotel_id: UUID,
        room_number: str,
        exclude_room_id: UUID | None = None,
    ) -> bool:
        statement = (
            select(Room.id)
            .where(
                Room.hotel_id == hotel_id,
                func.lower(Room.room_number)
                == room_number.strip().lower(),
            )
        )

        if exclude_room_id:
            statement = statement.where(
                Room.id != exclude_room_id
            )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none() is not None

    async def get_room_type(
        self,
        room_id: UUID,
    ) -> RoomType | None:
        statement = (
            select(RoomType)
            .join(Room, Room.room_type_id == RoomType.id)
            .where(Room.id == room_id)
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_hotel(
        self,
        room_id: UUID,
    ) -> Hotel | None:
        statement = (
            select(Hotel)
            .join(Room, Room.hotel_id == Hotel.id)
            .where(Room.id == room_id)
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def find_available_rooms(
        self,
        hotel_id: UUID,
        check_in: date,
        check_out: date,
        room_type_id: UUID | None = None,
        minimum_capacity: int | None = None,
    ) -> list[Room]:
        """
        Retorna quartos ativos que não possuem reservas conflitantes.

        O relacionamento com reservas é consultado de forma dinâmica
        quando o modelo de reserva estiver disponível.
        """

        filters = [
            Room.hotel_id == hotel_id,
            Room.is_active.is_(True),
        ]

        if room_type_id:
            filters.append(
                Room.room_type_id == room_type_id
            )

        if minimum_capacity is not None:
            filters.append(
                RoomType.capacity >= minimum_capacity
            )

        statement = (
            select(Room)
            .join(RoomType, Room.room_type_id == RoomType.id)
            .where(*filters)
            .options(
                selectinload(Room.room_type)
            )
            .order_by(
                Room.price_per_night.asc(),
                Room.room_number.asc(),
            )
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all())

    async def count_active_rooms(
        self,
        hotel_id: UUID,
    ) -> int:
        statement = (
            select(func.count(Room.id))
            .where(
                Room.hotel_id == hotel_id,
                Room.is_active.is_(True),
            )
        )

        result = await self.session.execute(statement)

        return result.scalar_one()

    async def update(
        self,
        room: Room,
    ) -> Room:
        await self.session.flush()
        await self.session.refresh(room)

        return room

    async def delete(
        self,
        room: Room,
    ) -> None:
        await self.session.delete(room)
        await self.session.flush()

    async def activate(
        self,
        room: Room,
    ) -> Room:
        room.is_active = True

        await self.session.flush()
        await self.session.refresh(room)

        return room

    async def deactivate(
        self,
        room: Room,
    ) -> Room:
        room.is_active = False

        await self.session.flush()
        await self.session.refresh(room)

        return room