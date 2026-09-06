import logging
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from src.core.database import AsyncSessionLocal
from src.models.transactions import Transaction, TransactionStatus
from src.repositories.transactions_repository import TransactionRepository
from src.services.gateway.gateway_factory import GatewayFactory
from src.services.payment_service import PaymentService, PaymentServiceError
from src.services.saga.payment_saga import PaymentSaga


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PaymentTaskResult:
    transaction_id: UUID
    status: TransactionStatus
    processed: bool
    error: str | None = None


async def process_payment(
    transaction_id: UUID,
) -> PaymentTaskResult:
    """
    Processa uma transação de pagamento em background.

    A task recupera a transação persistida e delega o processamento
    para o PaymentService, mantendo as regras financeiras fora
    da camada de worker.
    """

    logger.info(
        "Iniciando processamento assíncrono do pagamento | "
        "transaction_id=%s",
        transaction_id,
    )

    async with AsyncSessionLocal() as session:
        repository = TransactionRepository(session)

        transaction = await repository.get_by_id(
            transaction_id
        )

        if transaction is None:
            logger.error(
                "Transação não encontrada | transaction_id=%s",
                transaction_id,
            )

            return PaymentTaskResult(
                transaction_id=transaction_id,
                status=TransactionStatus.FAILED,
                processed=False,
                error="Transação não encontrada.",
            )

        if transaction.status in {
            TransactionStatus.SUCCEEDED,
            TransactionStatus.CANCELLED,
            TransactionStatus.REFUNDED,
        }:
            logger.info(
                "Transação já finalizada | transaction_id=%s | status=%s",
                transaction_id,
                transaction.status.value,
            )

            return PaymentTaskResult(
                transaction_id=transaction.id,
                status=transaction.status,
                processed=False,
            )

        try:
            gateway_factory = GatewayFactory()

            payment_service = PaymentService(
                session=session,
                gateway_factory=gateway_factory,
            )

            gateway = gateway_factory.get_gateway(
                transaction.provider
            )

            response = await gateway.get_payment(
                gateway_transaction_id=(
                    transaction.gateway_transaction_id
                    or ""
                ),
            )

            gateway_status = str(
                response.get("status", "")
            ).lower()

            if gateway_status in {
                "succeeded",
                "paid",
                "captured",
                "completed",
            }:
                transaction.status = TransactionStatus.SUCCEEDED

                captured_amount = response.get(
                    "captured_amount"
                )

                if captured_amount is not None:
                    transaction.captured_amount = Decimal(
                        str(captured_amount)
                    )

            elif gateway_status in {
                "failed",
                "declined",
                "rejected",
            }:
                transaction.status = TransactionStatus.FAILED
                transaction.failure_code = "gateway_failed"
                transaction.failure_message = (
                    "O gateway informou falha no pagamento."
                )

            elif gateway_status in {
                "cancelled",
                "canceled",
            }:
                transaction.status = TransactionStatus.CANCELLED

            else:
                transaction.status = TransactionStatus.PROCESSING

            await session.commit()

            logger.info(
                "Pagamento processado | transaction_id=%s | status=%s",
                transaction.id,
                transaction.status.value,
            )

            return PaymentTaskResult(
                transaction_id=transaction.id,
                status=transaction.status,
                processed=True,
            )

        except PaymentServiceError as exc:
            await session.rollback()

            logger.exception(
                "Falha no processamento do pagamento | "
                "transaction_id=%s",
                transaction_id,
            )

            return PaymentTaskResult(
                transaction_id=transaction_id,
                status=TransactionStatus.FAILED,
                processed=False,
                error=str(exc),
            )

        except Exception as exc:
            await session.rollback()

            logger.exception(
                "Erro inesperado no worker de pagamento | "
                "transaction_id=%s",
                transaction_id,
            )

            return PaymentTaskResult(
                transaction_id=transaction_id,
                status=TransactionStatus.FAILED,
                processed=False,
                error=str(exc),
            )


async def capture_authorized_payment(
    transaction_id: UUID,
    amount: Decimal | None = None,
) -> PaymentTaskResult:
    """
    Executa captura de uma transação previamente autorizada.
    """

    logger.info(
        "Iniciando captura assíncrona | transaction_id=%s",
        transaction_id,
    )

    async with AsyncSessionLocal() as session:
        repository = TransactionRepository(session)

        transaction = await repository.get_by_id(
            transaction_id
        )

        if transaction is None:
            return PaymentTaskResult(
                transaction_id=transaction_id,
                status=TransactionStatus.FAILED,
                processed=False,
                error="Transação não encontrada.",
            )

        if transaction.status != TransactionStatus.AUTHORIZED:
            return PaymentTaskResult(
                transaction_id=transaction.id,
                status=transaction.status,
                processed=False,
                error=(
                    "A transação não está autorizada "
                    "para captura."
                ),
            )

        try:
            payment_service = PaymentService(
                session=session,
                gateway_factory=GatewayFactory(),
            )

            saga = PaymentSaga(payment_service)

            transaction = await saga.capture(
                transaction_id=transaction.id,
                amount=amount,
            )

            return PaymentTaskResult(
                transaction_id=transaction.id,
                status=transaction.status,
                processed=True,
            )

        except Exception as exc:
            await session.rollback()

            logger.exception(
                "Falha na captura assíncrona | transaction_id=%s",
                transaction_id,
            )

            return PaymentTaskResult(
                transaction_id=transaction_id,
                status=TransactionStatus.FAILED,
                processed=False,
                error=str(exc),
            )


async def cancel_pending_payment(
    transaction_id: UUID,
) -> PaymentTaskResult:
    """
    Cancela uma transação pendente ou autorizada.
    """

    logger.info(
        "Iniciando cancelamento assíncrono | transaction_id=%s",
        transaction_id,
    )

    async with AsyncSessionLocal() as session:
        repository = TransactionRepository(session)

        transaction = await repository.get_by_id(
            transaction_id
        )

        if transaction is None:
            return PaymentTaskResult(
                transaction_id=transaction_id,
                status=TransactionStatus.FAILED,
                processed=False,
                error="Transação não encontrada.",
            )

        if transaction.status in {
            TransactionStatus.CANCELLED,
            TransactionStatus.SUCCEEDED,
            TransactionStatus.REFUNDED,
        }:
            return PaymentTaskResult(
                transaction_id=transaction.id,
                status=transaction.status,
                processed=False,
            )

        try:
            payment_service = PaymentService(
                session=session,
                gateway_factory=GatewayFactory(),
            )

            saga = PaymentSaga(payment_service)

            transaction = await saga.cancel(
                transaction_id=transaction.id,
            )

            return PaymentTaskResult(
                transaction_id=transaction.id,
                status=transaction.status,
                processed=True,
            )

        except Exception as exc:
            await session.rollback()

            logger.exception(
                "Falha no cancelamento assíncrono | transaction_id=%s",
                transaction_id,
            )

            return PaymentTaskResult(
                transaction_id=transaction_id,
                status=TransactionStatus.FAILED,
                processed=False,
                error=str(exc),
            )