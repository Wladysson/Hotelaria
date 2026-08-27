import logging
from abc import ABC, abstractmethod
from typing import Any


logger = logging.getLogger(
    "auth-service.subscribers"
)


class EventSubscriber(ABC):

    @abstractmethod
    async def handle(
        self,
        event_name: str,
        payload: dict[str, Any],
    ) -> None:
        raise NotImplementedError


class AuthEventSubscriber(
    EventSubscriber
):

    async def handle(
        self,
        event_name: str,
        payload: dict[str, Any],
    ) -> None:
        handlers = {
            "user.created": self._handle_user_created,
            "user.deleted": self._handle_user_deleted,
            "user.verified": self._handle_user_verified,
            "password.changed": self._handle_password_changed,
            "user.deactivated": self._handle_user_deactivated,
        }

        handler = handlers.get(event_name)

        if handler is None:
            logger.warning(
                "Unhandled authentication event: %s",
                event_name,
            )

            return

        await handler(payload)

    async def _handle_user_created(
        self,
        payload: dict[str, Any],
    ) -> None:
        logger.info(
            "Processing user.created event"
        )

    async def _handle_user_deleted(
        self,
        payload: dict[str, Any],
    ) -> None:
        logger.info(
            "Processing user.deleted event"
        )

    async def _handle_user_verified(
        self,
        payload: dict[str, Any],
    ) -> None:
        logger.info(
            "Processing user.verified event"
        )

    async def _handle_password_changed(
        self,
        payload: dict[str, Any],
    ) -> None:
        logger.info(
            "Processing password.changed event"
        )

    async def _handle_user_deactivated(
        self,
        payload: dict[str, Any],
    ) -> None:
        logger.info(
            "Processing user.deactivated event"
        )