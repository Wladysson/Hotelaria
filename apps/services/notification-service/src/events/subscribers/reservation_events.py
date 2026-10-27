import logging
from typing import Any

from src.core.config import settings


logger = logging.getLogger(__name__)


class ReservationEventHandler:
    async def handle(self, event: dict[str, Any]) -> None:
        event_type = event.get("event_type")

        if not event_type:
            logger.warning("Evento de reserva recebido sem event_type")
            return

        logger.info(
            "Processando evento de reserva: %s",
            event_type,
        )

        await self._process(event_type, event)

    async def _process(
        self,
        event_type: str,
        event: dict[str, Any],
    ) -> None:
        if event_type in {
            "reservation.created",
            "reservation.confirmed",
            "reservation.cancelled",
            "reservation.completed",
        }:
            logger.info(
                "Evento de reserva elegível para notificação: %s",
                event_type,
            )
            return

        logger.debug(
            "Evento de reserva ignorado: %s",
            event_type,
        )