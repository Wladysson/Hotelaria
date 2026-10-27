import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.notification import (
    Notification,
    NotificationStatus,
    NotificationType,
)
from src.repositories.notification_repository import NotificationRepository
from src.schemas.notifications import (
    NotificationCreate,
    NotificationUpdate,
)


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = NotificationRepository(session)

    async def create(
        self,
        data: NotificationCreate,
    ) -> Notification:
        notification = Notification(
            recipient=data.recipient,
            subject=data.subject,
            content=data.content,
            notification_type=data.notification_type,
            provider=data.provider,
        )

        return await self.repository.create(notification)

    async def get_by_id(
        self,
        notification_id: uuid.UUID,
    ) -> Notification:
        notification = await self.repository.get_by_id(notification_id)

        if notification is None:
            raise ValueError("Notificação não encontrada")

        return notification

    async def list(
        self,
        *,
        status: NotificationStatus | None = None,
        notification_type: NotificationType | None = None,
        recipient: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Notification]:
        return await self.repository.list(
            status=status,
            notification_type=notification_type,
            recipient=recipient,
            skip=skip,
            limit=limit,
        )

    async def update(
        self,
        notification_id: uuid.UUID,
        data: NotificationUpdate,
    ) -> Notification:
        notification = await self.get_by_id(notification_id)

        updates = data.model_dump(exclude_unset=True)

        for field, value in updates.items():
            setattr(notification, field, value)

        return await self.repository.update(notification)

    async def mark_as_processing(
        self,
        notification_id: uuid.UUID,
    ) -> Notification:
        notification = await self.get_by_id(notification_id)

        notification.mark_as_processing()

        return await self.repository.update(notification)

    async def mark_as_sent(
        self,
        notification_id: uuid.UUID,
        provider_message_id: str | None = None,
    ) -> Notification:
        notification = await self.get_by_id(notification_id)

        notification.mark_as_sent(provider_message_id)

        return await self.repository.update(notification)

    async def mark_as_failed(
        self,
        notification_id: uuid.UUID,
        error_message: str,
    ) -> Notification:
        notification = await self.get_by_id(notification_id)

        notification.mark_as_failed(error_message)

        return await self.repository.update(notification)

    async def cancel(
        self,
        notification_id: uuid.UUID,
    ) -> Notification:
        notification = await self.get_by_id(notification_id)

        notification.status = NotificationStatus.CANCELLED

        return await self.repository.update(notification)