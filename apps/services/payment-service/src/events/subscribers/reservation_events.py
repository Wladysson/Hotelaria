from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from src.models.transactions import TransactionStatus
from src.schemas.payment import PaymentCreate
from src.services.payment_service import PaymentService
from src.services.saga.payment_saga import PaymentSaga


class ReservationEventType(str, Enum):
    CREATED = "reservation.created"
    CONFIRMED = "reservation.confirmed"
    CANCELLED = "reservation.cancelled"
    EXPIRED = "reservation.expired"


@dataclass(slots=True)
class ReservationEvent:
    event_id: UUID
    event_type: ReservationEventType
    reservation_id: UUID
    customer_id: UUID
    amount: Decimal
    currency: str
    payment_method_id: UUID
    provider: str
    idempotency_key: str
    description: str | None = None
    metadata: dict[str, str] | None = None


class ReservationEventHandler:
    """
    Processa eventos relacionados ao ciclo de vida das reservas.

    O subscriber traduz eventos externos do reservation-service
    em comandos internos para o fluxo de pagamentos.
    """

    def __init__(
        self,
        payment_service: PaymentService,
    ):
        self.payment_service = payment_service
        self.payment_saga = PaymentSaga(payment_service)

    async def handle(
        self,
        event: ReservationEvent,
    ) -> None:
        handlers = {
            ReservationEventType.CREATED: self.handle_reservation_created,
            ReservationEventType.CONFIRMED: self.handle_reservation_confirmed,
            ReservationEventType.CANCELLED: self.handle_reservation_cancelled,
            ReservationEventType.EXPIRED: self.handle_reservation_expired,
        }

        handler = handlers.get(event.event_type)

        if handler is None:
            raise ValueError(
                f"Evento de reserva não suportado: "
                f"{event.event_type.value}"
            )

        await handler(event)

    async def handle_reservation_created(
        self,
        event: ReservationEvent,
    ) -> None:
        """
        Processa a criação de uma reserva.

        Dependendo da política de negócio, a criação pode
        iniciar o fluxo de autorização do pagamento.
        """

        payment_data = PaymentCreate(
            reservation_id=event.reservation_id,
            customer_id=event.customer_id,
            amount=event.amount,
            currency=event.currency,
            payment_method_id=event.payment_method_id,
            provider=event.provider,
            description=event.description,
            requires_capture=True,
            idempotency_key=event.idempotency_key,
            metadata={
                **(event.metadata or {}),
                "reservation_event_id": str(event.event_id),
                "reservation_event_type": event.event_type.value,
            },
        )

        await self.payment_saga.execute(payment_data)

    async def handle_reservation_confirmed(
        self,
        event: ReservationEvent,
    ) -> None:
        """
        Processa a confirmação de uma reserva.

        A confirmação pode representar o momento em que
        um pagamento previamente autorizado deve ser capturado.
        """

        transaction = await self.payment_service.transaction_repository.get_by_idempotency_key(
            event.idempotency_key
        )

        if transaction is None:
            return

        if transaction.status != TransactionStatus.AUTHORIZED:
            return

        await self.payment_saga.capture(
            transaction_id=transaction.id,
        )

    async def handle_reservation_cancelled(
        self,
        event: ReservationEvent,
    ) -> None:
        """
        Cancela uma autorização de pagamento associada à reserva.
        """

        transactions = (
            await self.payment_service.transaction_repository.list_by_reservation(
                event.reservation_id,
                offset=0,
                limit=100,
            )
        )

        for transaction in transactions:
            if transaction.status in {
                TransactionStatus.PENDING,
                TransactionStatus.AUTHORIZED,
                TransactionStatus.PROCESSING,
            }:
                await self.payment_saga.cancel(
                    transaction_id=transaction.id,
                )

    async def handle_reservation_expired(
        self,
        event: ReservationEvent,
    ) -> None:
        """
        Trata reservas expiradas.

        O comportamento é equivalente à compensação de uma
        reserva cancelada quando existe autorização financeira.
        """

        await self.handle_reservation_cancelled(event)


def build_reservation_event(
    payload: dict[str, Any],
) -> ReservationEvent:
    """
    Converte o payload recebido do broker para o contrato interno.
    """

    return ReservationEvent(
        event_id=UUID(str(payload["event_id"])),
        event_type=ReservationEventType(
            payload["event_type"]
        ),
        reservation_id=UUID(
            str(payload["reservation_id"])
        ),
        customer_id=UUID(
            str(payload["customer_id"])
        ),
        amount=Decimal(
            str(payload["amount"])
        ),
        currency=str(
            payload.get("currency", "BRL")
        ).upper(),
        payment_method_id=UUID(
            str(payload["payment_method_id"])
        ),
        provider=str(
            payload["provider"]
        ).lower(),
        idempotency_key=str(
            payload["idempotency_key"]
        ),
        description=payload.get("description"),
        metadata=payload.get("metadata"),
    )
