from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.city import City
from src.models.hotel import Hotel
from src.models.room import Room


class HotelRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        hotel: Hotel,
    ) -> Hotel:
        self.session.add(hotel)

        await self.session.flush()
        await self.session.refresh(hotel)

        return hotel

    async def get_by_id(
        self,
        hotel_id: UUID,
    ) -> Hotel | None:
        statement = (
            select(Hotel)
            .where(Hotel.id == hotel_id)
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_by_id_detailed(
        self,
        hotel_id: UUID,
    ) -> Hotel | None:
        statement = (
            select(Hotel)
            .options(
                selectinload(Hotel.city),
                selectinload(Hotel.rooms),
                selectinload(Hotel.amenities),
                selectinload(Hotel.images),
            )
            .where(Hotel.id == hotel_id)
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_by_id_with_rooms(
        self,
        hotel_id: UUID,
    ) -> Hotel | None:
        statement = (
            select(Hotel)
            .options(
                selectinload(Hotel.rooms)
            )
            .where(Hotel.id == hotel_id)
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_by_name(
        self,
        name: str,
    ) -> Hotel | None:
        statement = (
            select(Hotel)
            .where(
                func.lower(Hotel.name) == name.strip().lower()
            )
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        city_id: UUID | None = None,
        is_active: bool | None = True,
        min_rating: int | None = None,
        max_rating: int | None = None,
    ) -> tuple[list[Hotel], int]:
        offset = (page - 1) * page_size

        filters = []

        if city_id:
            filters.append(
                Hotel.city_id == city_id
            )

        if is_active is not None:
            filters.append(
                Hotel.is_active == is_active
            )

        if min_rating is not None:
            filters.append(
                Hotel.star_rating >= min_rating
            )

        if max_rating is not None:
            filters.append(
                Hotel.star_rating <= max_rating
            )

        count_statement = (
            select(func.count(Hotel.id))
            .where(*filters)
        )

        total_result = await self.session.execute(
            count_statement
        )

        total = total_result.scalar_one()

        statement = (
            select(Hotel)
            .where(*filters)
            .order_by(
                Hotel.star_rating.desc(),
                Hotel.name.asc(),
            )
            .offset(offset)
            .limit(page_size)
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all()), total

    async def list_by_city(
        self,
        city_id: UUID,
        page: int = 1,
        page_size: int = 20,
        is_active: bool = True,
    ) -> tuple[list[Hotel], int]:
        return await self.list(
            page=page,
            page_size=page_size,
            city_id=city_id,
            is_active=is_active,
        )

    async def exists(
        self,
        hotel_id: UUID,
    ) -> bool:
        statement = (
            select(Hotel.id)
            .where(Hotel.id == hotel_id)
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none() is not None

    async def exists_by_name(
        self,
        name: str,
        city_id: UUID,
        exclude_hotel_id: UUID | None = None,
    ) -> bool:
        statement = (
            select(Hotel.id)
            .where(
                func.lower(Hotel.name) == name.strip().lower(),
                Hotel.city_id == city_id,
            )
        )

        if exclude_hotel_id:
            statement = statement.where(
                Hotel.id != exclude_hotel_id
            )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none() is not None

    async def get_city(
        self,
        hotel_id: UUID,
    ) -> City | None:
        statement = (
            select(City)
            .join(Hotel, Hotel.city_id == City.id)
            .where(Hotel.id == hotel_id)
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_available_room_count(
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
        hotel: Hotel,
    ) -> Hotel:
        await self.session.flush()
        await self.session.refresh(hotel)

        return hotel

    async def delete(
        self,
        hotel: Hotel,
    ) -> None:
        await self.session.delete(hotel)
        await self.session.flush()

    async def activate(
        self,
        hotel: Hotel,
    ) -> Hotel:
        hotel.is_active = True

        await self.session.flush()
        await self.session.refresh(hotel)

        return hotel

    async def deactivate(
        self,
        hotel: Hotel,
    ) -> Hotel:
        hotel.is_active = False

        await self.session.flush()
        await self.session.refresh(hotel)

        return hotel