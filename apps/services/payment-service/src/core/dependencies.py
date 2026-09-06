from collections.abc import AsyncGenerator

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_session


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db_session():
        yield session


def pagination_params(
    page: int = Query(
        default=1,
        ge=1,
        description="Número da página.",
    ),
    size: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Quantidade de registros por página.",
    ),
) -> dict[str, int]:
    return {
        "page": page,
        "size": size,
        "offset": (page - 1) * size,
        "limit": size,
    }