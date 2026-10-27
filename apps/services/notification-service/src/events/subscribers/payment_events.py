import logging
from typing import Any


logger = logging.getLogger(__name__)


class PaymentEventHandler:
    async def handle(self, event: dict[str, Any]) -> None:
        event_type = event.get("event_type")

        if not event_type:
            logger.warning("Evento de pagamento recebido sem event_type")
            return

        logger.info(
            "Processando evento de pagamento: %s",
            event_type,
        )

        await self._process(event_type, event)

    async def _process(
        self,
        event_type: str,
        event: dict[str, Any],
    ) -> None:
        if event_type in {
            "payment.approved",
            "payment.failed",
            "payment.refunded",
            "payment.cancelled",
        }:
            logger.info(
                "Evento de pagamento elegível para notificação: %s",
                event_type,
            )
            return

        logger.debug(
            "Evento de pagamento ignorado: %s",
            event_type,
        )
