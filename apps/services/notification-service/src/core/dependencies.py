from collections.abc import AsyncGenerator

from aio_pika import AbstractRobustConnection, RobustConnection, connect_robust

from src.core.config import settings


async def get_rabbitmq_connection() -> AsyncGenerator[AbstractRobustConnection, None]:
    connection: RobustConnection | None = None

    try:
        connection = await connect_robust(
            settings.RABBITMQ_URL,
            timeout=settings.RABBITMQ_CONNECTION_TIMEOUT,
        )

        yield connection

    finally:
        if connection and not connection.is_closed:
            await connection.close()