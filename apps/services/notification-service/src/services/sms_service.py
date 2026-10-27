import uuid

import httpx

from src.core.config import settings
from src.models.notification import Notification
from src.services.notification_service import NotificationService


class SMSService:
    def __init__(
        self,
        notification_service: NotificationService,
    ) -> None:
        self.notification_service = notification_service

    async def send(
        self,
        notification_id: uuid.UUID,
    ) -> Notification:
        notification = await self.notification_service.get_by_id(
            notification_id,
        )

        if not settings.SEND_SMS_ENABLED:
            raise RuntimeError(
                "Envio de SMS está desabilitado",
            )

        if not settings.SMS_API_URL:
            raise RuntimeError(
                "SMS_API_URL não configurada",
            )

        if not settings.SMS_API_KEY:
            raise RuntimeError(
                "SMS_API_KEY não configurada",
            )

        await self.notification_service.mark_as_processing(
            notification.id,
        )

        try:
            async with httpx.AsyncClient(
                timeout=settings.NOTIFICATION_RETRY_DELAY,
            ) as client:
                response = await client.post(
                    settings.SMS_API_URL,
                    headers={
                        "Authorization": f"Bearer {settings.SMS_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "to": notification.recipient,
                        "message": notification.content,
                    },
                )

                response.raise_for_status()

                response_data = response.json()

            provider_message_id = response_data.get("message_id")

            return await self.notification_service.mark_as_sent(
                notification.id,
                provider_message_id=provider_message_id,
            )

        except Exception as exc:
            await self.notification_service.mark_as_failed(
                notification.id,
                str(exc),
            )
            raise