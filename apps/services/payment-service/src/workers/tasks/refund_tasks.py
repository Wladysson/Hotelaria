import logging
from dataclasses import dataclass
from uuid import UUID

from src.core.database import AsyncSessionLocal
from src.models.refund import Refund, RefundStatus
from src.services.gateway.gateway_factory import GatewayFactory
from src.services.refund_service import RefundService
from src.services.saga.refund_saga import RefundSaga


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RefundTaskResult:
    refund_id: UUID
    status: RefundStatus
    processed: bool
    error: str | None = None


async def process_refund(
    refund_id: UUID,
) -> RefundTaskResult:
    """
    Monitora e processa um reembolso em background.

    Reembolsos podem permanecer em processamento no gateway,
    portanto a task permite verificar o estado externo
    e sincronizar o resultado local.
    """

    logger.info(
        "Iniciando processamento assíncrono do reembolso | "
        "refund_id=%s",
        refund_id,
    )

    async with AsyncSessionLocal() as session:
        result = await session.get(
            Refund,
            refund_id,
        )

        if result is None:
            logger.error(
                "Reembolso não encontrado | refund_id=%s",
                refund_id,
            )

            return RefundTaskResult(
                refund_id=refund_id,
                status=RefundStatus.FAILED,
                processed=False,
                error="Reembolso não encontrado.",
            )

        refund = result

        if refund.status == RefundStatus.SUCCEEDED:
            return RefundTaskResult(
                refund_id=refund.id,
                status=refund.status,
                processed=False,
            )

        if refund.status == RefundStatus.CANCELLED:
            return RefundTaskResult(
                refund_id=refund.id,
                status=refund.status,
                processed=False,
            )

        try:
            if refund.status == RefundStatus.FAILED:
                logger.info(
                    "Reembolso já marcado como falho | refund_id=%s",
                    refund.id,
                )

                return RefundTaskResult(
                    refund_id=refund.id,
                    status=refund.status,
                    processed=False,
                )

            refund.status = RefundStatus.PROCESSING

            await session.commit()

            logger.info(
                "Reembolso marcado para processamento | refund_id=%s",
                refund.id,
            )

            return RefundTaskResult(
                refund_id=refund.id,
                status=refund.status,
                processed=True,
            )

        except Exception as exc:
            await session.rollback()

            logger.exception(
                "Falha no processamento do reembolso | refund_id=%s",
                refund_id,
            )

            return RefundTaskResult(
                refund_id=refund_id,
                status=RefundStatus.FAILED,
                processed=False,
                error=str(exc),
            )


async def retry_refund(
    refund_id: UUID,
) -> RefundTaskResult:
    """
    Reprocessa um reembolso que apresentou falha transitória.

    A tarefa mantém o identificador original do reembolso,
    evitando a criação de uma nova operação financeira.
    """

    logger.info(
        "Iniciando retry de reembolso | refund_id=%s",
        refund_id,
    )

    async with AsyncSessionLocal() as session:
        refund = await session.get(
            Refund,
            refund_id,
        )

        if refund is None:
            return RefundTaskResult(
                refund_id=refund_id,
                status=RefundStatus.FAILED,
                processed=False,
                error="Reembolso não encontrado.",
            )

        if refund.status == RefundStatus.SUCCEEDED:
            return RefundTaskResult(
                refund_id=refund.id,
                status=refund.status,
                processed=False,
            )

        refund.status = RefundStatus.PROCESSING

        await session.commit()

        return RefundTaskResult(
            refund_id=refund.id,
            status=refund.status,
            processed=True,
        )


async def cancel_pending_refund(
    refund_id: UUID,
) -> RefundTaskResult:
    """
    Cancela um reembolso que ainda não foi concluído.

    A operação é limitada ao estado local do processo.
    O cancelamento efetivo no provedor depende do suporte
    específico de cada gateway.
    """

    logger.info(
        "Cancelando reembolso pendente | refund_id=%s",
        refund_id,
    )

    async with AsyncSessionLocal() as session:
        refund = await session.get(
            Refund,
            refund_id,
        )

        if refund is None:
            return RefundTaskResult(
                refund_id=refund_id,
                status=RefundStatus.FAILED,
                processed=False,
                error="Reembolso não encontrado.",
            )

        if refund.status in {
            RefundStatus.SUCCEEDED,
            RefundStatus.FAILED,
            RefundStatus.CANCELLED,
        }:
            return RefundTaskResult(
                refund_id=refund.id,
                status=refund.status,
                processed=False,
            )

        refund.status = RefundStatus.CANCELLED

        await session.commit()

        return RefundTaskResult(
            refund_id=refund.id,
            status=refund.status,
            processed=True,
        )