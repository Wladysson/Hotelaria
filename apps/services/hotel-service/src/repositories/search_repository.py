from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.amenity import Amenity
from src.models.city import City
from src.models.hotel import Hotel
from src.models.image import Image
from src.models.room import Room
from src.models.room_type import RoomType


class SearchRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def search_hotels(
        self,
        check_in: date,
        check_out: date,
        guests: int,
        rooms: int,
        city_id: UUID | None = None,
        city_name: str | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        min_rating: int | None = None,
        star_rating: int | None = None,
        amenity_ids: list[UUID] | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Hotel], int]:
        """
        Pesquisa hotéis com quartos compatíveis com os filtros.

        A consulta considera:
        - cidade;
        - classificação;
        - preço;
        - capacidade;
        - quantidade de quartos;
        - comodidades;
        - status ativo.
        """

        filters = [
            Hotel.is_active.is_(True),
            Room.is_active.is_(True),
            RoomType.capacity >= guests,
        ]

        if city_id:
            filters.append(
                Hotel.city_id == city_id
            )

        if city_name:
            filters.append(
                func.lower(City.name).like(
                    f"%{city_name.strip().lower()}%"
                )
            )

        if min_price is not None:
            filters.append(
                Room.price_per_night >= min_price
            )

        if max_price is not None:
            filters.append(
                Room.price_per_night <= max_price
            )

        if min_rating is not None:
            filters.append(
                Hotel.star_rating >= min_rating
            )

        if star_rating is not None:
            filters.append(
                Hotel.star_rating == star_rating
            )

        statement = (
            select(Hotel)
            .join(City, Hotel.city_id == City.id)
            .join(Room, Room.hotel_id == Hotel.id)
            .join(RoomType, Room.room_type_id == RoomType.id)
            .where(*filters)
        )

        if amenity_ids:
            amenity_count = len(amenity_ids)

            statement = (
                statement
                .join(
                    Hotel.amenities
                )
                .where(
                    Amenity.id.in_(amenity_ids)
                )
                .group_by(Hotel.id)
                .having(
                    func.count(
                        func.distinct(Amenity.id)
                    ) == amenity_count
                )
            )

        statement = statement.distinct()

        count_statement = select(
            func.count()
        ).select_from(
            statement.subquery()
        )

        total_result = await self.session.execute(
            count_statement
        )

        total = total_result.scalar_one()

        offset = (page - 1) * page_size

        statement = (
            statement
            .options(
                selectinload(Hotel.city),
                selectinload(Hotel.rooms)
                .selectinload(Room.room_type),
                selectinload(Hotel.images),
                selectinload(Hotel.amenities),
            )
            .order_by(
                Hotel.star_rating.desc(),
                Hotel.name.asc(),
            )
            .offset(offset)
            .limit(page_size)
        )

        result = await self.session.execute(statement)

        return list(result.scalars().unique().all()), total

    async def get_available_rooms(
        self,
        check_in: date,
        check_out: date,
        guests: int,
        rooms: int,
        hotel_id: UUID | None = None,
        city_id: UUID | None = None,
        room_type_id: UUID | None = None,
    ) -> list[Room]:
        filters = [
            Hotel.is_active.is_(True),
            Room.is_active.is_(True),
            RoomType.capacity >= guests,
        ]

        if hotel_id:
            filters.append(
                Hotel.id == hotel_id
            )

        if city_id:
            filters.append(
                Hotel.city_id == city_id
            )

        if room_type_id:
            filters.append(
                Room.room_type_id == room_type_id
            )

        statement = (
            select(Room)
            .join(Hotel, Room.hotel_id == Hotel.id)
            .join(RoomType, Room.room_type_id == RoomType.id)
            .where(*filters)
            .options(
                selectinload(Room.hotel),
                selectinload(Room.room_type),
            )
            .order_by(
                Room.price_per_night.asc(),
                Hotel.name.asc(),
                Room.room_number.asc(),
            )
        )

        result = await self.session.execute(statement)

        return list(result.scalars().unique().all())

    async def get_hotel_lowest_price(
        self,
        hotel_id: UUID,
    ) -> Decimal | None:
        statement = (
            select(func.min(Room.price_per_night))
            .where(
                Room.hotel_id == hotel_id,
                Room.is_active.is_(True),
            )
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def count_available_rooms(
        self,
        hotel_id: UUID,
        guests: int,
    ) -> int:
        statement = (
            select(func.count(Room.id))
            .join(
                RoomType,
                Room.room_type_id == RoomType.id,
            )
            .where(
                Room.hotel_id == hotel_id,
                Room.is_active.is_(True),
                RoomType.capacity >= guests,
            )
        )

        result = await self.session.execute(statement)

        return result.scalar_one()

    async def get_hotel_primary_image(
        self,
        hotel_id: UUID,
    ) -> Image | None:
        statement = (
            select(Image)
            .where(
                Image.hotel_id == hotel_id
            )
            .order_by(
                Image.is_primary.desc(),
                Image.position.asc(),
            )
            .limit(1)
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_hotels_by_city(
        self,
        city_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Hotel], int]:
        offset = (page - 1) * page_size

        count_statement = (
            select(func.count(Hotel.id))
            .where(
                Hotel.city_id == city_id,
                Hotel.is_active.is_(True),
            )
        )

        total_result = await self.session.execute(
            count_statement
        )

        total = total_result.scalar_one()

        statement = (
            select(Hotel)
            .where(
                Hotel.city_id == city_id,
                Hotel.is_active.is_(True),
            )
            .options(
                selectinload(Hotel.city),
                selectinload(Hotel.images),
            )
            .order_by(
                Hotel.star_rating.desc(),
                Hotel.name.asc(),
            )
            .offset(offset)
            .limit(page_size)
        )

        result = await self.session.execute(statement)

        return list(result.scalars().unique().all()), total