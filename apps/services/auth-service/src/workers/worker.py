import asyncio
import logging

from shared.messaging.rabbitmq_client import RabbitMQClient

logger = logging.getLogger(__name__)


class AuthWorker:

    def __init__(self, rabbitmq: RabbitMQClient):
        self.rabbitmq = rabbitmq

    async def start(self) -> None:
        logger.info("Starting auth-service worker")

        await self.rabbitmq.connect()

        await self.rabbitmq.consume(
            queue="auth-service",
            callback=self.handle_message,
        )

    async def handle_message(self, message: dict) -> None:
        event_name = message.get("event_name")

        logger.info(
            "Received auth-service event: %s",
            event_name,
        )

        # Eventos específicos serão registrados conforme
        # os casos de uso assíncronos do serviço forem implementados.

    async def stop(self) -> None:
        logger.info("Stopping auth-service worker")

        await self.rabbitmq.close()


async def run_worker(rabbitmq: RabbitMQClient) -> None:
    worker = AuthWorker(rabbitmq)

    try:
        await worker.start()

    except asyncio.CancelledError:
        logger.info("Auth-service worker cancelled")
        raise

    except Exception:
        logger.exception("Auth-service worker stopped unexpectedly")
        raise

    finally:
        await worker.stop()