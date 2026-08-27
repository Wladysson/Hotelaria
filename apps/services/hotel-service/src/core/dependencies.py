from collections.abc import AsyncGenerator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_session
from fastapi import Header, HTTPException, status

from src.repositories.city_repository import CityRepository
from src.repositories.hotel_repository import HotelRepository
from src.repositories.room_repository import RoomRepository
from src.repositories.search_repository import SearchRepository

from src.services.availability_service import AvailabilityService
from src.services.hotel_service import HotelService
from src.services.room_service import RoomService
from src.services.search_service import SearchService


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Fornece uma sessão assíncrona do PostgreSQL.
    """

    async for session in get_db_session():
        yield session


def get_city_repository(
    session: AsyncSession = Depends(get_session),
) -> CityRepository:
    """
    Fornece o repositório de cidades.
    """

    return CityRepository(session)


def get_hotel_repository(
    session: AsyncSession = Depends(get_session),
) -> HotelRepository:
    """
    Fornece o repositório de hotéis.
    """

    return HotelRepository(session)


def get_room_repository(
    session: AsyncSession = Depends(get_session),
) -> RoomRepository:
    """
    Fornece o repositório de quartos.
    """

    return RoomRepository(session)


def get_search_repository(
    session: AsyncSession = Depends(get_session),
) -> SearchRepository:
    """
    Fornece o repositório de pesquisas.
    """

    return SearchRepository(session)


def get_hotel_service(
    hotel_repository: HotelRepository = Depends(
        get_hotel_repository
    ),
    city_repository: CityRepository = Depends(
        get_city_repository
    ),
) -> HotelService:
    """
    Fornece o serviço de hotéis.
    """

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
    """
    Fornece o serviço de quartos.
    """

    return RoomService(
        room_repository=room_repository,
        hotel_repository=hotel_repository,
    )


def get_search_service(
    search_repository: SearchRepository = Depends(
        get_search_repository
    ),
) -> SearchService:
    """
    Fornece o serviço de pesquisa.
    """

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
    """
    Fornece o serviço de disponibilidade.
    """

    return AvailabilityService(
        room_repository=room_repository,
        hotel_repository=hotel_repository,
    )


async def get_current_user(
    authorization: str | None = Header(default=None),
) -> dict[str, object]:
    """
    Obtém a identidade do usuário autenticado.
    """

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação não informado.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Esquema de autenticação inválido.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    token = authorization.removeprefix("Bearer ").strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação inválido.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    return {
        "authenticated": True,
        "token": token,
    }