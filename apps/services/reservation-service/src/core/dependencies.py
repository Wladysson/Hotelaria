from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.cache import Cache, get_cache
from src.core.database import get_db_session


async def get_session() -> AsyncGenerator[
    AsyncSession,
    None,
]:
    """
    Fornece uma sessão assíncrona do PostgreSQL
    para as dependências da aplicação.
    """

    async for session in get_db_session():
        yield session


async def get_redis(
    cache: Cache = Depends(get_cache),
) -> Cache:
    """
    Fornece acesso ao cache Redis.
    """

    return cache