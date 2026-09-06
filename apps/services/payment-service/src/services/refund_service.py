from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.payment_gateway import PaymentGatewayError
from src.models.refund import Refund, RefundStatus
from src.models.transactions import Transaction, TransactionStatus
from src.repositories.transactions_repository import TransactionRepository
from src.schemas.refund import RefundCreate


class RefundServiceError(Exception):
    """Erro base das regras de negócio de reembolso."""


class RefundNotFoundError(RefundServiceError):
    """Indica que o reembolso não foi encontrado."""


class RefundAlreadyProcessedError(RefundServiceError):
    """Indica que a solicitação de reembolso já foi processada."""


class RefundAmountExceededError(RefundServiceError):
    """Indica que o valor solicitado excede o valor disponível."""


class RefundNotAllowedError(RefundServiceError):
    """Indica que a transação não permite reembolso."""


class RefundService:
    def __init__(
        self,
        session: AsyncSession,
        gateway_factory,
    ):
        self.session = session
        self.gateway_factory = gateway_factory
        self.transaction_repository = TransactionRepository(session)

    async def create_refund(
        self,
        data: RefundCreate,
    ) -> Refund:
        existing_refund = await self._get_by_idempotency_key(
            data.idempotency_key
        )

        if existing_refund:
            raise RefundAlreadyProcessedError(
                "A chave de idempotência já foi utilizada em um reembolso."
            )

        transaction = (
            await self.transaction_repository.get_by_id(
                data.transaction_id
            )
        )

        if transaction is None:
            raise RefundServiceError(
                "Transação original não encontrada."
            )

        self._validate_refundable_transaction(transaction)

        available_amount = (
            transaction.captured_amount
            - transaction.refunded_amount
        )

        if data.amount > available_amount:
            raise RefundAmountExceededError(
                "O valor solicitado excede o valor disponível para reembolso."
            )

        refund = Refund(
            transaction_id=transaction.id,
            reservation_id=data.reservation_id,
            amount=data.amount,
            currency=transaction.currency,
            status=RefundStatus.PENDING,
            reason=data.reason,
            idempotency_key=data.idempotency_key,
        )

        self.session.add(refund)
        await self.session.flush()
        await self.session.refresh(refund)

        if not transaction.gateway_transaction_id:
            raise RefundServiceError(
                "A transação não possui identificador no gateway."
            )

        gateway = self.gateway_factory.get_gateway(
            transaction.provider
        )

        try:
            response = await gateway.refund_payment(
                gateway_transaction_id=(
                    transaction.gateway_transaction_id
                ),
                amount=data.amount,
                reason=data.reason.value,
            )

            refund.status = self._resolve_refund_status(
                response
            )

            refund.gateway_refund_id = (
                response.get("gateway_refund_id")
                or response.get("id")
            )

            if refund.status == RefundStatus.SUCCEEDED:
                transaction.refunded_amount += data.amount

                if transaction.refunded_amount >= transaction.amount:
                    transaction.status = TransactionStatus.REFUNDED
                else:
                    transaction.status = (
                        TransactionStatus.PARTIALLY_REFUNDED
                    )

            await self.session.flush()
            await self.session.commit()

            return refund

        except PaymentGatewayError as exc:
            refund.status = RefundStatus.FAILED
            refund.failure_code = "gateway_error"
            refund.failure_message = str(exc)

            await self.session.flush()
            await self.session.commit()

            raise RefundServiceError(
                "Falha ao processar o reembolso no gateway."
            ) from exc

    async def get_refund(
        self,
        refund_id: UUID,
    ) -> Refund:
        result = await self.session.execute(
            select(Refund).where(
                Refund.id == refund_id,
            )
        )

        refund = result.scalar_one_or_none()

        if refund is None:
            raise RefundNotFoundError(
                "Reembolso não encontrado."
            )

        return refund

    async def get_refund_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> Refund | None:
        return await self._get_by_idempotency_key(
            idempotency_key
        )

    async def _get_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> Refund | None:
        result = await self.session.execute(
            select(Refund).where(
                Refund.idempotency_key == idempotency_key,
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    def _validate_refundable_transaction(
        transaction: Transaction,
    ) -> None:
        refundable_statuses = {
            TransactionStatus.SUCCEEDED,
            TransactionStatus.PARTIALLY_REFUNDED,
        }

        if transaction.status not in refundable_statuses:
            raise RefundNotAllowedError(
                "A transação não está em um estado que permita reembolso."
            )

        if transaction.captured_amount <= Decimal("0.00"):
            raise RefundNotAllowedError(
                "A transação não possui valor capturado para reembolso."
            )

    @staticmethod
    def _resolve_refund_status(
        gateway_response: dict,
    ) -> RefundStatus:
        status = str(
            gateway_response.get("status", "")
        ).lower()

        if status in {
            "succeeded",
            "refunded",
            "completed",
            "processed",
        }:
            return RefundStatus.SUCCEEDED

        if status in {
            "failed",
            "declined",
            "rejected",
        }:
            return RefundStatus.FAILED

        return RefundStatus.PROCESSING