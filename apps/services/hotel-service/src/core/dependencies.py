from collections.abc import AsyncGenerator

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.cache import Cache, get_cache
from src.core.config import settings
from src.core.database import get_db_session


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Fornece uma sessão assíncrona do PostgreSQL.
    """

    async for session in get_db_session():
        yield session


async def get_redis(
    cache: Cache = Depends(get_cache),
) -> Cache:
    """
    Fornece acesso ao Redis.
    """

    return cache


def pagination_params(
    page: int = Query(
        default=1,
        ge=1,
        description="Número da página.",
    ),
    size: int = Query(
        default=settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description="Quantidade de registros por página.",
    ),
) -> dict[str, int]:
    """
    Centraliza os parâmetros de paginação da API.
    """

    return {
        "page": page,
        "size": size,
        "offset": (page - 1) * size,
        "limit": size,
    }