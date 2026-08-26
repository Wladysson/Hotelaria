from typing import Any

from shared.messaging.message_bus import MessageBus


class EventPublisher:

    def __init__(self, message_bus: MessageBus):
        self.message_bus = message_bus

    async def publish(
        self,
        event_name: str,
        payload: dict[str, Any],
    ) -> None:
        await self.message_bus.publish(
            event_name=event_name,
            payload=payload,
        )