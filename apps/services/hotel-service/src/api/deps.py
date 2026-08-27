from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.city_repository import CityRepository
from src.repositories.hotel_repository import HotelRepository
from src.repositories.room_repository import RoomRepository
from src.repositories.search_repository import SearchRepository
from src.services.availability_service import AvailabilityService
from src.services.hotel_services import HotelService
from src.services.room_services import RoomService
from src.services.search_services import SearchService


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session


def get_city_repository(
    session: AsyncSession = Depends(get_session),
) -> CityRepository:
    return CityRepository(session)


def get_hotel_repository(
    session: AsyncSession = Depends(get_session),
) -> HotelRepository:
    return HotelRepository(session)


def get_room_repository(
    session: AsyncSession = Depends(get_session),
) -> RoomRepository:
    return RoomRepository(session)


def get_search_repository(
    session: AsyncSession = Depends(get_session),
) -> SearchRepository:
    return SearchRepository(session)


def get_hotel_service(
    hotel_repository: HotelRepository = Depends(
        get_hotel_repository
    ),
    city_repository: CityRepository = Depends(
        get_city_repository
    ),
) -> HotelService:
    return HotelService(
        hotel_repository=hotel_repository,
        city_repository=city_repository,
    )


def get_room_service(
    room_repository: RoomRepository = Depends(
        get_room_repository
    ),
    hotel_repository: HotelRepository = Depends(
        get_hotel_repository
    ),
) -> RoomService:
    return RoomService(
        room_repository=room_repository,
        hotel_repository=hotel_repository,
    )


def get_search_service(
    search_repository: SearchRepository = Depends(
        get_search_repository
    ),
) -> SearchService:
    return SearchService(
        search_repository=search_repository,
    )


def get_availability_service(
    room_repository: RoomRepository = Depends(
        get_room_repository
    ),
    hotel_repository: HotelRepository = Depends(
        get_hotel_repository
    ),
) -> AvailabilityService:
    return AvailabilityService(
        room_repository=room_repository,
        hotel_repository=hotel_repository,
    )