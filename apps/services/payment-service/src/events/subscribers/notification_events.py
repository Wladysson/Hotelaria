from dataclasses import dataclass
from enum import Enum
from typing import Any
from uuid import UUID

from src.services.payment_service import PaymentService


class NotificationEventType(str, Enum):
    SENT = "notification.sent"
    FAILED = "notification.failed"
    DELIVERED = "notification.delivered"


@dataclass(slots=True)
class NotificationEvent:
    event_id: UUID
    event_type: NotificationEventType
    notification_id: UUID
    transaction_id: UUID | None = None
    customer_id: UUID | None = None
    channel: str | None = None
    template: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    metadata: dict[str, Any] | None = None


class NotificationEventHandler:
    """
    Processa eventos de retorno relacionados às notificações
    associadas às operações financeiras.

    O handler não envia notificações diretamente. A responsabilidade
    de envio permanece no notification-service.
    """

    def __init__(
        self,
        payment_service: PaymentService,
    ):
        self.payment_service = payment_service

    async def handle(
        self,
        event: NotificationEvent,
    ) -> None:
        handlers = {
            NotificationEventType.SENT: self.handle_notification_sent,
            NotificationEventType.FAILED: self.handle_notification_failed,
            NotificationEventType.DELIVERED: self.handle_notification_delivered,
        }

        handler = handlers.get(event.event_type)

        if handler is None:
            raise ValueError(
                f"Evento de notificação não suportado: "
                f"{event.event_type.value}"
            )

        await handler(event)

    async def handle_notification_sent(
        self,
        event: NotificationEvent,
    ) -> None:
        """
        Processa confirmação de envio da notificação.

        O estado financeiro da transação não é alterado,
        pois envio de notificação não representa mudança
        no processamento financeiro.
        """

        if event.transaction_id is None:
            return

        transaction = await self.payment_service.get_payment(
            event.transaction_id
        )

        if transaction is None:
            return

    async def handle_notification_delivered(
        self,
        event: NotificationEvent,
    ) -> None:
        """
        Processa confirmação de entrega da notificação.

        A confirmação de entrega é usada apenas para
        rastreabilidade e não altera o estado financeiro.
        """

        if event.transaction_id is None:
            return

        transaction = await self.payment_service.get_payment(
            event.transaction_id
        )

        if transaction is None:
            return

    async def handle_notification_failed(
        self,
        event: NotificationEvent,
    ) -> None:
        """
        Processa falhas de entrega de notificações.

        Uma falha de notificação não deve cancelar ou
        estornar automaticamente uma transação financeira.
        """

        if event.transaction_id is None:
            return

        transaction = await self.payment_service.get_payment(
            event.transaction_id
        )

        if transaction is None:
            return

        # Falha de notificação não altera o estado financeiro.


def build_notification_event(
    payload: dict[str, Any],
) -> NotificationEvent:
    """
    Converte o payload recebido do broker para o contrato interno.
    """

    transaction_id = payload.get("transaction_id")
    customer_id = payload.get("customer_id")

    return NotificationEvent(
        event_id=UUID(
            str(payload["event_id"])
        ),
        event_type=NotificationEventType(
            payload["event_type"]
        ),
        notification_id=UUID(
            str(payload["notification_id"])
        ),
        transaction_id=(
            UUID(str(transaction_id))
            if transaction_id
            else None
        ),
        customer_id=(
            UUID(str(customer_id))
            if customer_id
            else None
        ),
        channel=payload.get("channel"),
        template=payload.get("template"),
        error_code=payload.get("error_code"),
        error_message=payload.get("error_message"),
        metadata=payload.get("metadata"),
    )