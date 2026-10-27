import uuid

from src.core.email_provider import EmailProvider
from src.models.notification import Notification
from src.services.notification_service import NotificationService


class EmailService:
    def __init__(
        self,
        notification_service: NotificationService,
        email_provider: EmailProvider,
    ) -> None:
        self.notification_service = notification_service
        self.email_provider = email_provider

    async def send(
        self,
        notification_id: uuid.UUID,
    ) -> Notification:
        notification = await self.notification_service.get_by_id(
            notification_id,
        )

        await self.notification_service.mark_as_processing(
            notification.id,
        )

        try:
            await self.email_provider.send(
                recipient=notification.recipient,
                subject=notification.subject or "",
                body=notification.content,
            )

            return await self.notification_service.mark_as_sent(
                notification.id,
            )

        except Exception as exc:
            await self.notification_service.mark_as_failed(
                notification.id,
                str(exc),
            )
            raise