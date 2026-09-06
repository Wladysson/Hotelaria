from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.payment_gateway import (
    PaymentGatewayDeclinedError,
    PaymentGatewayError,
    PaymentGatewayTimeoutError,
)
from src.models.transactions import (
    PaymentProvider,
    Transaction,
    TransactionStatus,
    TransactionType,
)
from src.repositories.payment_method_repository import PaymentMethodRepository
from src.repositories.transactions_repository import TransactionRepository
from src.schemas.payment import PaymentCreate


class PaymentServiceError(Exception):
    """Erro base das regras de negócio de pagamentos."""


class PaymentAlreadyProcessedError(PaymentServiceError):
    """Indica que a chave de idempotência já foi processada."""


class TransactionNotFoundError(PaymentServiceError):
    """Indica que a transação solicitada não existe."""


class PaymentMethodNotFoundError(PaymentServiceError):
    """Indica que o método de pagamento não existe."""


class InvalidTransactionStateError(PaymentServiceError):
    """Indica que a operação não pode ser executada no estado atual."""


class PaymentService:
    def __init__(
        self,
        session: AsyncSession,
        gateway_factory,
    ):
        self.session = session
        self.transaction_repository = TransactionRepository(session)
        self.payment_method_repository = PaymentMethodRepository(session)
        self.gateway_factory = gateway_factory

    async def create_payment(
        self,
        data: PaymentCreate,
    ) -> Transaction:
        existing_transaction = (
            await self.transaction_repository.get_by_idempotency_key(
                data.idempotency_key
            )
        )

        if existing_transaction:
            raise PaymentAlreadyProcessedError(
                "A chave de idempotência já foi processada."
            )

        payment_method = (
            await self.payment_method_repository.get_by_id(
                data.payment_method_id
            )
        )

        if payment_method is None:
            raise PaymentMethodNotFoundError(
                "Método de pagamento não encontrado."
            )

        transaction = Transaction(
            reservation_id=data.reservation_id,
            customer_id=data.customer_id,
            amount=data.amount,
            currency=data.currency.upper(),
            transaction_type=TransactionType.PAYMENT,
            status=TransactionStatus.PENDING,
            provider=data.provider,
            idempotency_key=data.idempotency_key,
            description=data.description,
            requires_capture=data.requires_capture,
            metadata_json=data.metadata,
        )

        await self.transaction_repository.create(transaction)

        try:
            gateway = self.gateway_factory.get_gateway(data.provider)

            gateway_response = await gateway.create_payment(
                transaction_id=str(transaction.id),
                amount=data.amount,
                currency=data.currency.upper(),
                payment_method=str(data.payment_method_id),
                description=data.description,
                metadata=data.metadata,
            )

            transaction.status = self._resolve_payment_status(
                gateway_response,
                data.requires_capture,
            )

            transaction.gateway_transaction_id = (
                gateway_response.get("gateway_transaction_id")
                or gateway_response.get("id")
            )

            if gateway_response.get("captured_amount") is not None:
                transaction.captured_amount = Decimal(
                    str(gateway_response["captured_amount"])
                )

            await self.transaction_repository.update(
                transaction,
                status=transaction.status,
                gateway_transaction_id=transaction.gateway_transaction_id,
                captured_amount=transaction.captured_amount,
            )

            await self.session.commit()

            return transaction

        except PaymentGatewayDeclinedError as exc:
            await self._mark_failed(
                transaction,
                "payment_declined",
                str(exc),
            )
            raise PaymentServiceError(
                "O pagamento foi recusado pelo gateway."
            ) from exc

        except PaymentGatewayTimeoutError as exc:
            await self._mark_failed(
                transaction,
                "gateway_timeout",
                str(exc),
            )
            raise PaymentServiceError(
                "O gateway excedeu o tempo limite de processamento."
            ) from exc

        except PaymentGatewayError as exc:
            await self._mark_failed(
                transaction,
                "gateway_error",
                str(exc),
            )
            raise PaymentServiceError(
                "Falha no processamento do pagamento."
            ) from exc

    async def capture_payment(
        self,
        transaction_id,
        amount: Decimal | None = None,
    ) -> Transaction:
        transaction = await self._get_transaction(transaction_id)

        if transaction.status != TransactionStatus.AUTHORIZED:
            raise InvalidTransactionStateError(
                "Somente pagamentos autorizados podem ser capturados."
            )

        if not transaction.gateway_transaction_id:
            raise PaymentServiceError(
                "A transação não possui identificador no gateway."
            )

        gateway = self.gateway_factory.get_gateway(
            transaction.provider
        )

        try:
            response = await gateway.capture_payment(
                gateway_transaction_id=transaction.gateway_transaction_id,
                amount=amount,
            )

            captured_amount = Decimal(
                str(
                    response.get(
                        "captured_amount",
                        amount or transaction.amount,
                    )
                )
            )

            transaction.captured_amount = captured_amount
            transaction.status = TransactionStatus.SUCCEEDED

            await self.transaction_repository.update(
                transaction,
                status=transaction.status,
                captured_amount=captured_amount,
            )

            await self.session.commit()

            return transaction

        except PaymentGatewayError as exc:
            await self._mark_failed(
                transaction,
                "capture_failed",
                str(exc),
            )

            raise PaymentServiceError(
                "Falha ao capturar o pagamento."
            ) from exc

    async def cancel_payment(
        self,
        transaction_id,
    ) -> Transaction:
        transaction = await self._get_transaction(transaction_id)

        cancellable_statuses = {
            TransactionStatus.PENDING,
            TransactionStatus.AUTHORIZED,
            TransactionStatus.PROCESSING,
        }

        if transaction.status not in cancellable_statuses:
            raise InvalidTransactionStateError(
                "A transação não pode ser cancelada no estado atual."
            )

        if not transaction.gateway_transaction_id:
            transaction.status = TransactionStatus.CANCELLED

            await self.transaction_repository.update(
                transaction,
                status=transaction.status,
            )

            await self.session.commit()

            return transaction

        gateway = self.gateway_factory.get_gateway(
            transaction.provider
        )

        try:
            await gateway.cancel_payment(
                gateway_transaction_id=transaction.gateway_transaction_id,
            )

            transaction.status = TransactionStatus.CANCELLED

            await self.transaction_repository.update(
                transaction,
                status=transaction.status,
            )

            await self.session.commit()

            return transaction

        except PaymentGatewayError as exc:
            raise PaymentServiceError(
                "Falha ao cancelar o pagamento no gateway."
            ) from exc

    async def get_payment(
        self,
        transaction_id,
    ) -> Transaction:
        return await self._get_transaction(transaction_id)

    async def _get_transaction(
        self,
        transaction_id,
    ) -> Transaction:
        transaction = await self.transaction_repository.get_by_id(
            transaction_id
        )

        if transaction is None:
            raise TransactionNotFoundError(
                "Transação não encontrada."
            )

        return transaction

    async def _mark_failed(
        self,
        transaction: Transaction,
        failure_code: str,
        failure_message: str,
    ) -> None:
        transaction.status = TransactionStatus.FAILED
        transaction.failure_code = failure_code
        transaction.failure_message = failure_message

        await self.transaction_repository.update(
            transaction,
            status=transaction.status,
            failure_code=failure_code,
            failure_message=failure_message,
        )

        await self.session.commit()

    @staticmethod
    def _resolve_payment_status(
        gateway_response: dict,
        requires_capture: bool,
    ) -> TransactionStatus:
        gateway_status = str(
            gateway_response.get("status", "")
        ).lower()

        if gateway_status in {"declined", "failed", "rejected"}:
            return TransactionStatus.FAILED

        if requires_capture:
            return TransactionStatus.AUTHORIZED

        if gateway_status in {
            "succeeded",
            "paid",
            "captured",
            "completed",
        }:
            return TransactionStatus.SUCCEEDED

        return TransactionStatus.PROCESSING