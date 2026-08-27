from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.city import City


class CityRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, city: City) -> City:
        self.session.add(city)

        await self.session.flush()
        await self.session.refresh(city)

        return city

    async def get_by_id(
        self,
        city_id: UUID,
    ) -> City | None:
        statement = (
            select(City)
            .where(City.id == city_id)
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_by_name(
        self,
        name: str,
        state: str | None = None,
    ) -> City | None:
        statement = (
            select(City)
            .where(
                func.lower(City.name) == name.strip().lower()
            )
        )

        if state:
            statement = statement.where(
                func.lower(City.state) == state.strip().lower()
            )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        state: str | None = None,
        search: str | None = None,
    ) -> tuple[list[City], int]:
        offset = (page - 1) * page_size

        filters = []

        if state:
            filters.append(
                func.lower(City.state) == state.strip().lower()
            )

        if search:
            search_pattern = f"%{search.strip().lower()}%"

            filters.append(
                func.lower(City.name).like(search_pattern)
            )

        count_statement = (
            select(func.count(City.id))
            .where(*filters)
        )

        total_result = await self.session.execute(
            count_statement
        )

        total = total_result.scalar_one()

        statement = (
            select(City)
            .where(*filters)
            .order_by(City.name.asc())
            .offset(offset)
            .limit(page_size)
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all()), total

    async def exists(
        self,
        city_id: UUID,
    ) -> bool:
        statement = (
            select(City.id)
            .where(City.id == city_id)
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none() is not None

    async def exists_by_name(
        self,
        name: str,
        state: str,
        exclude_city_id: UUID | None = None,
    ) -> bool:
        statement = (
            select(City.id)
            .where(
                func.lower(City.name) == name.strip().lower(),
                func.lower(City.state) == state.strip().lower(),
            )
        )

        if exclude_city_id:
            statement = statement.where(
                City.id != exclude_city_id
            )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none() is not None

    async def update(
        self,
        city: City,
    ) -> City:
        await self.session.flush()
        await self.session.refresh(city)

        return city

    async def delete(
        self,
        city: City,
    ) -> None:
        await self.session.delete(city)
        await self.session.flush()