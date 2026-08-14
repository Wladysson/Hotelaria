import logging
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select

from src.core.database import AsyncSessionLocal
from src.models.refund import Refund, RefundStatus
from src.models.transactions import (
    PaymentProvider,
    Transaction,
    TransactionStatus,
)
from src.services.gateway.gateway_factory import GatewayFactory


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ReconciliationResult:
    transaction_id: UUID
    internal_status: TransactionStatus
    external_status: str
    reconciled: bool
    discrepancy: str | None = None


async def reconcile_transaction(
    transaction_id: UUID,
) -> ReconciliationResult:
    """
    Compara o estado da transação local com o gateway.

    A reconciliação é uma camada de segurança operacional para
    identificar divergências causadas por timeouts, falhas de rede,
    callbacks perdidos ou processamento assíncrono do provedor.
    """

    logger.info(
        "Iniciando reconciliação | transaction_id=%s",
        transaction_id,
    )

    async with AsyncSessionLocal() as session:
        transaction = await session.get(
            Transaction,
            transaction_id,
        )

        if transaction is None:
            raise ValueError(
                f"Transação não encontrada: {transaction_id}"
            )

        if transaction.provider is None:
            raise ValueError(
                "A transação não possui provedor de pagamento."
            )

        if not transaction.gateway_transaction_id:
            raise ValueError(
                "A transação não possui identificador externo."
            )

        gateway_factory = GatewayFactory()

        gateway = gateway_factory.get_gateway(
            transaction.provider
        )

        response = await gateway.get_payment(
            gateway_transaction_id=(
                transaction.gateway_transaction_id
            ),
        )

        external_status = str(
            response.get("status", "")
        ).lower()

        normalized_status = _normalize_external_status(
            external_status
        )

        discrepancy = _detect_discrepancy(
            internal_status=transaction.status,
            external_status=normalized_status,
        )

        reconciled = discrepancy is None

        if reconciled:
            _synchronize_transaction(
                transaction=transaction,
                gateway_response=response,
                external_status=normalized_status,
            )

            await session.commit()

        else:
            logger.warning(
                "Divergência encontrada | "
                "transaction_id=%s | internal=%s | external=%s",
                transaction.id,
                transaction.status.value,
                normalized_status.value,
            )

        return ReconciliationResult(
            transaction_id=transaction.id,
            internal_status=transaction.status,
            external_status=external_status,
            reconciled=reconciled,
            discrepancy=discrepancy,
        )


async def reconcile_pending_transactions(
    limit: int = 100,
) -> list[ReconciliationResult]:
    """
    Reconcilia transações que ainda não alcançaram um estado terminal.
    """

    if limit < 1:
        raise ValueError(
            "O limite de reconciliação deve ser maior que zero."
        )

    if limit > 1000:
        raise ValueError(
            "O limite máximo de reconciliação é 1000."
        )

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Transaction)
            .where(
                Transaction.status.in_(
                    [
                        TransactionStatus.PENDING,
                        TransactionStatus.AUTHORIZED,
                        TransactionStatus.PROCESSING,
                    ]
                )
            )
            .order_by(Transaction.created_at.asc())
            .limit(limit)
        )

        transactions = list(
            result.scalars().all()
        )

    reconciliation_results: list[ReconciliationResult] = []

    for transaction in transactions:
        try:
            result = await reconcile_transaction(
                transaction.id
            )
            reconciliation_results.append(result)

        except Exception as exc:
            logger.exception(
                "Falha na reconciliação | transaction_id=%s",
                transaction.id,
            )

            reconciliation_results.append(
                ReconciliationResult(
                    transaction_id=transaction.id,
                    internal_status=transaction.status,
                    external_status="unknown",
                    reconciled=False,
                    discrepancy=str(exc),
                )
            )

    return reconciliation_results


async def reconcile_refund(
    refund_id: UUID,
) -> bool:
    """
    Verifica se um reembolso possui estado consistente.

    A consulta externa específica do refund dependerá do contrato
    de gateway utilizado. Por isso, a task valida inicialmente
    a consistência local e a presença dos identificadores externos.
    """

    async with AsyncSessionLocal() as session:
        refund = await session.get(
            Refund,
            refund_id,
        )

        if refund is None:
            raise ValueError(
                f"Reembolso não encontrado: {refund_id}"
            )

        if refund.status == RefundStatus.SUCCEEDED:
            return True

        if not refund.gateway_refund_id:
            logger.warning(
                "Reembolso sem identificador externo | refund_id=%s",
                refund.id,
            )
            return False

        return refund.status in {
            RefundStatus.PROCESSING,
            RefundStatus.SUCCEEDED,
        }


def _normalize_external_status(
    status: str,
) -> TransactionStatus:
    if status in {
        "succeeded",
        "paid",
        "captured",
        "completed",
    }:
        return TransactionStatus.SUCCEEDED

    if status in {
        "authorized",
        "requires_capture",
    }:
        return TransactionStatus.AUTHORIZED

    if status in {
        "failed",
        "declined",
        "rejected",
    }:
        return TransactionStatus.FAILED

    if status in {
        "cancelled",
        "canceled",
    }:
        return TransactionStatus.CANCELLED

    return TransactionStatus.PROCESSING


def _detect_discrepancy(
    *,
    internal_status: TransactionStatus,
    external_status: TransactionStatus,
) -> str | None:
    if internal_status == external_status:
        return None

    terminal_states = {
        TransactionStatus.SUCCEEDED,
        TransactionStatus.FAILED,
        TransactionStatus.CANCELLED,
    }

    if (
        internal_status in terminal_states
        and external_status != internal_status
    ):
        return (
            "Estado terminal interno divergente do estado "
            "retornado pelo gateway."
        )

    if (
        internal_status == TransactionStatus.AUTHORIZED
        and external_status == TransactionStatus.SUCCEEDED
    ):
        return None

    if (
        internal_status == TransactionStatus.PROCESSING
        and external_status
        in {
            TransactionStatus.SUCCEEDED,
            TransactionStatus.FAILED,
            TransactionStatus.CANCELLED,
        }
    ):
        return None

    return (
        "Estado interno e estado externo apresentam "
        "diferença que requer análise."
    )


def _synchronize_transaction(
    *,
    transaction: Transaction,
    gateway_response: dict,
    external_status: TransactionStatus,
) -> None:
    transaction.status = external_status

    captured_amount = gateway_response.get(
        "captured_amount"
    )

    if captured_amount is not None:
        transaction.captured_amount = Decimal(
            str(captured_amount)
        )