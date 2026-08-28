from typing import Any

from redis.asyncio import Redis

from src.core.config import settings


class Cache:
    """
    Abstração assíncrona sobre o Redis.

    Centraliza operações de cache utilizadas pelo serviço,
    evitando acesso direto ao cliente Redis nas demais camadas.
    """

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def get(self, key: str) -> Any:
        """
        Recupera um valor armazenado no Redis.
        """

        return await self._redis.get(key)

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """
        Armazena um valor no Redis com TTL opcional.
        """

        expire = (
            ttl
            if ttl is not None
            else settings.CACHE_TTL_SECONDS
        )

        return await self._redis.set(
            key,
            value,
            ex=expire,
        )

    async def delete(self, key: str) -> int:
        """
        Remove uma chave do Redis.
        """

        return await self._redis.delete(key)

    async def exists(self, key: str) -> bool:
        """
        Verifica se uma chave existe no Redis.
        """

        return bool(await self._redis.exists(key))

    async def expire(
        self,
        key: str,
        ttl: int,
    ) -> bool:
        """
        Atualiza o TTL de uma chave existente.
        """

        return bool(
            await self._redis.expire(
                key,
                ttl,
            )
        )

    async def close(self) -> None:
        """
        Fecha a conexão com o Redis.
        """

        await self._redis.aclose()


def create_cache() -> Cache:
    """
    Cria a instância do cache Redis.
    """

    redis = Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )

    return Cache(redis)


cache = create_cache()


def get_cache() -> Cache:
    """
    Dependency responsável por fornecer o cache Redis.
    """

    return cache