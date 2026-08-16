import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.notification import (
    Notification,
    NotificationStatus,
    NotificationType,
)

class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        notification: Notification,
    ) -> Notification:
        self.session.add(notification)
        await self.session.flush()
        await self.session.refresh(notification)

        return notification

    async def get_by_id(
        self,
        notification_id: uuid.UUID,
    ) -> Notification | None:
        result = await self.session.execute(
            select(Notification).where(
                Notification.id == notification_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_by_provider_message_id(
        self,
        provider_message_id: str,
    ) -> Notification | None:
        result = await self.session.execute(
            select(Notification).where(
                Notification.provider_message_id
                == provider_message_id,
            )
        )

        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        status: NotificationStatus | None = None,
        notification_type: NotificationType | None = None,
        recipient: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Notification]:
        query = select(Notification)

        if status is not None:
            query = query.where(Notification.status == status)

        if notification_type is not None:
            query = query.where(
                Notification.notification_type == notification_type
            )

        if recipient is not None:
            query = query.where(Notification.recipient == recipient)

        query = (
            query
            .order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(query)

        return list(result.scalars().all())

    async def count(
        self,
        *,
        status: NotificationStatus | None = None,
        notification_type: NotificationType | None = None,
        recipient: str | None = None,
    ) -> int:
        query = select(func.count(Notification.id))

        if status is not None:
            query = query.where(Notification.status == status)

        if notification_type is not None:
            query = query.where(
                Notification.notification_type == notification_type
            )

        if recipient is not None:
            query = query.where(Notification.recipient == recipient)

        result = await self.session.execute(query)

        return result.scalar_one()

    async def update(
        self,
        notification: Notification,
    ) -> Notification:
        await self.session.flush()
        await self.session.refresh(notification)

        return notification

    async def delete(
        self,
        notification: Notification,
    ) -> None:
        await self.session.delete(notification)
        await self.session.flush()