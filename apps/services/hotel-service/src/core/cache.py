from typing import Any

from redis.asyncio import Redis
from redis.asyncio.connection import ConnectionPool

from src.core.config import settings


class Cache:
    """
    Abstração assíncrona sobre o Redis.
    """

    def __init__(self) -> None:
        self._pool: ConnectionPool | None = None
        self._redis: Redis | None = None

    async def connect(self) -> None:
        """
        Inicializa o pool e a conexão com o Redis.
        """

        if self._redis is not None:
            return

        self._pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            decode_responses=True,
        )

        self._redis = Redis(
            connection_pool=self._pool,
        )

        await self._redis.ping()

    async def close(self) -> None:
        """
        Encerra a conexão com o Redis.
        """

        if self._redis is not None:
            await self._redis.aclose()

        self._redis = None

        if self._pool is not None:
            await self._pool.aclose()

        self._pool = None

    def _client(self) -> Redis:
        if self._redis is None:
            raise RuntimeError(
                "Redis não foi inicializado. "
                "Execute cache.connect() antes de utilizar o cache."
            )

        return self._redis

    async def get(
        self,
        key: str,
    ) -> str | None:
        """
        Recupera um valor armazenado.
        """

        return await self._client().get(key)

    async def set(
        self,
        key: str,
        value: str,
        ttl: int | None = None,
    ) -> bool:
        """
        Armazena um valor no Redis.
        """

        if ttl is None:
            ttl = settings.CACHE_DEFAULT_TTL

        return bool(
            await self._client().set(
                key,
                value,
                ex=ttl,
            )
        )

    async def delete(
        self,
        key: str,
    ) -> int:
        """
        Remove uma chave do cache.
        """

        return await self._client().delete(key)

    async def exists(
        self,
        key: str,
    ) -> bool:
        """
        Verifica se uma chave existe.
        """

        return bool(
            await self._client().exists(key)
        )

    async def expire(
        self,
        key: str,
        ttl: int,
    ) -> bool:
        """
        Atualiza o TTL de uma chave.
        """

        return bool(
            await self._client().expire(
                key,
                ttl,
            )
        )

    async def clear_pattern(
        self,
        pattern: str,
    ) -> int:
        """
        Remove todas as chaves que correspondem ao padrão informado.

        Exemplo:

            hotel:123:*
        """

        client = self._client()
        deleted = 0

        async for key in client.scan_iter(
            match=pattern,
            count=100,
        ):
            deleted += await client.delete(key)

        return deleted

    async def health_check(self) -> bool:
        """
        Verifica a disponibilidade do Redis.
        """

        try:
            await self._client().ping()
            return True
        except Exception:
            return False


cache = Cache()


async def get_cache() -> Cache:
    """
    Dependency para acesso ao cache.
    """

    return cache