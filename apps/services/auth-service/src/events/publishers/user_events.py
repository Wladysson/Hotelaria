from uuid import UUID

from src.events.publishers.event_publisher import EventPublisher


class UserEventPublisher:

    def __init__(self, publisher: EventPublisher):
        self.publisher = publisher

    async def publish_user_created(
        self,
        user_id: UUID,
        email: str,
        role: str,
    ) -> None:
        await self.publisher.publish(
            event_name="USER_CREATED",
            payload={
                "user_id": str(user_id),
                "email": email,
                "role": role,
            },
        )

    async def publish_user_deactivated(
        self,
        user_id: UUID,
    ) -> None:
        await self.publisher.publish(
            event_name="USER_DEACTIVATED",
            payload={
                "user_id": str(user_id),
            },
        )