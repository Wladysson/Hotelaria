import asyncio
import logging

from src.core.config import settings


logger = logging.getLogger(__name__)


class NotificationWorker:
    def __init__(self) -> None:
        self.running = False

    async def start(self) -> None:
        if self.running:
            logger.warning("Notification worker já está em execução")
            return

        self.running = True

        logger.info(
            "Iniciando notification worker | environment=%s",
            settings.ENVIRONMENT,
        )

        try:
            while self.running:
                await self.process_pending_tasks()
                await asyncio.sleep(
                    settings.NOTIFICATION_RETRY_DELAY,
                )
        except asyncio.CancelledError:
            logger.info("Notification worker recebeu sinal de cancelamento")
            raise
        finally:
            self.running = False
            logger.info("Notification worker finalizado")

    async def stop(self) -> None:
        self.running = False
        logger.info("Solicitação de parada do notification worker")

    async def process_pending_tasks(self) -> None:
        logger.debug("Verificando tarefas pendentes de notificações")