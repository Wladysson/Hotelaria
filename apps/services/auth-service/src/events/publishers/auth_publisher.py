import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from uuid import UUID


logger = logging.getLogger(
    "auth-service.events"
)


class EventPublisher(ABC):

    @abstractmethod
    async def publish(
        self,
        event_name: str,
        payload: dict[str, Any],
    ) -> None:
        raise NotImplementedError


class AuthEventPublisher(
    EventPublisher
):

    async def publish(
        self,
        event_name: str,
        payload: dict[str, Any],
    ) -> None:
        event = {
            "event_id": str(UUID(int=__import__("uuid").uuid4().int)),
            "event_name": event_name,
            "occurred_at": datetime.utcnow().isoformat(),
            "payload": payload,
        }

        logger.info(
            "Authentication event generated: %s",
            event_name,
        )

        await self._dispatch(event)

    async def _dispatch(
        self,
        event: dict[str, Any],
    ) -> None:
        logger.debug(
            "Event pending broker dispatch: %s",
            event["event_name"],
        )