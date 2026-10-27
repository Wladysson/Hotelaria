import logging
from typing import Any


logger = logging.getLogger(__name__)


class AuthEventHandler:
    async def handle(self, event: dict[str, Any]) -> None:
        event_type = event.get("event_type")

        if not event_type:
            logger.warning("Evento de autenticação recebido sem event_type")
            return

        logger.info(
            "Processando evento de autenticação: %s",
            event_type,
        )

        await self._process(event_type, event)

    async def _process(
        self,
        event_type: str,
        event: dict[str, Any],
    ) -> None:
        if event_type in {
            "auth.user_registered",
            "auth.password_changed",
            "auth.password_reset_requested",
            "auth.account_locked",
            "auth.account_unlocked",
        }:
            logger.info(
                "Evento de autenticação elegível para notificação: %s",
                event_type,
            )
            return

        logger.debug(
            "Evento de autenticação ignorado: %s",
            event_type,
        )