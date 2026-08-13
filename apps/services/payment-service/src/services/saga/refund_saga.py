from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from src.models.refund import Refund, RefundStatus
from src.schemas.refund import RefundCreate
from src.services.refund_service import (
    RefundAlreadyProcessedError,
    RefundNotAllowedError,
    RefundService,
    RefundServiceError,
)


class RefundSagaError(Exception):
    """Erro base do fluxo distribuído de reembolso."""


class RefundSagaCompensationError(RefundSagaError):
    """Erro durante uma ação compensatória de reembolso."""


class RefundSaga:
    """
    Orquestra o processo distribuído de reembolso.

    O reembolso possui comportamento diferente do pagamento:
    a operação pode ser processada de forma assíncrona pelo gateway
    e o resultado final pode ser confirmado posteriormente por evento.
    """

    def __init__(self, refund_service: RefundService):
        self.refund_service = refund_service

    async def execute(
        self,
        data: RefundCreate,
    ) -> Refund:
        existing_refund = (
            await self.refund_service.get_refund_by_idempotency_key(
                data.idempotency_key
            )
        )

        if existing_refund is not None:
            return existing_refund

        try:
            refund = await self.refund_service.create_refund(data)

            if refund.status == RefundStatus.FAILED:
                raise RefundSagaError(
                    "O gateway recusou o processamento do reembolso."
                )

            return refund

        except RefundAlreadyProcessedError:
            existing_refund = (
                await self.refund_service.get_refund_by_idempotency_key(
                    data.idempotency_key
                )
            )

            if existing_refund is not None:
                return existing_refund

            raise RefundSagaError(
                "O reembolso já foi processado, mas não foi "
                "possível recuperar seu registro."
            )

        except RefundNotAllowedError as exc:
            raise RefundSagaError(
                "A transação não permite a execução do reembolso."
            ) from exc

        except RefundServiceError as exc:
            raise RefundSagaError(
                "Não foi possível concluir o fluxo de reembolso."
            ) from exc

    async def retry(
        self,
        data: RefundCreate,
    ) -> Refund:
        """
        Reprocessa uma solicitação de reembolso.

        A operação utiliza a chave de idempotência para impedir
        a criação de múltiplos reembolsos para a mesma solicitação.
        """

        existing_refund = (
            await self.refund_service.get_refund_by_idempotency_key(
                data.idempotency_key
            )
        )

        if existing_refund is not None:
            if existing_refund.status == RefundStatus.SUCCEEDED:
                return existing_refund

            if existing_refund.status == RefundStatus.PROCESSING:
                return existing_refund

        return await self.execute(data)

    async def get_status(
        self,
        refund_id: UUID,
    ) -> Refund:
        try:
            return await self.refund_service.get_refund(
                refund_id
            )
        except RefundServiceError as exc:
            raise RefundSagaError(
                "Não foi possível consultar o estado do reembolso."
            ) from exc

    async def handle_gateway_failure(
        self,
        refund_id: UUID,
        failure_code: str,
        failure_message: str,
    ) -> Refund:
        """
        Registra conceitualmente uma falha definitiva do gateway.

        A atualização persistente do estado permanece sob
        responsabilidade do serviço de domínio/persistência.
        """

        refund = await self.get_status(refund_id)

        if refund.status == RefundStatus.SUCCEEDED:
            return refund

        refund.status = RefundStatus.FAILED
        refund.failure_code = failure_code
        refund.failure_message = failure_message

        return refund

    @staticmethod
    def is_completed(
        refund: Refund,
    ) -> bool:
        return refund.status == RefundStatus.SUCCEEDED

    @staticmethod
    def requires_follow_up(
        refund: Refund,
    ) -> bool:
        return refund.status == RefundStatus.PROCESSING


@dataclass(slots=True)
class RefundSagaResult:
    """
    Resultado estruturado da execução da saga de reembolso.
    """

    refund_id: UUID
    transaction_id: UUID
    status: RefundStatus
    amount: Decimal
    completed: bool = False
    requires_follow_up: bool = False