from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from src.models.transactions import PaymentProvider, Transaction, TransactionStatus
from src.schemas.payment import PaymentCreate
from src.services.payment_service import (
    InvalidTransactionStateError,
    PaymentService,
    PaymentServiceError,
)


class PaymentSagaError(Exception):
    """Erro base do fluxo transacional de pagamento."""


class PaymentSagaCompensationError(PaymentSagaError):
    """Erro durante a compensação de um pagamento."""


class PaymentSaga:
    """
    Orquestra o fluxo distribuído de pagamento.

    A saga coordena as etapas do processo e define ações
    de compensação quando uma etapa posterior falha.
    """

    def __init__(self, payment_service: PaymentService):
        self.payment_service = payment_service

    async def execute(
        self,
        data: PaymentCreate,
    ) -> Transaction:
        transaction = await self._create_payment(data)

        if transaction.status == TransactionStatus.SUCCEEDED:
            return transaction

        if transaction.status == TransactionStatus.AUTHORIZED:
            return transaction

        if transaction.status in {
            TransactionStatus.FAILED,
            TransactionStatus.CANCELLED,
        }:
            raise PaymentSagaError(
                "O fluxo da saga de pagamento foi encerrado "
                "sem sucesso."
            )

        return transaction

    async def capture(
        self,
        transaction_id: UUID,
        amount: Decimal | None = None,
    ) -> Transaction:
        transaction = await self.payment_service.get_payment(
            transaction_id
        )

        if transaction.status != TransactionStatus.AUTHORIZED:
            raise InvalidTransactionStateError(
                "Somente pagamentos autorizados podem ser capturados."
            )

        try:
            return await self.payment_service.capture_payment(
                transaction_id=transaction_id,
                amount=amount,
            )
        except PaymentServiceError as exc:
            await self._compensate_capture_failure(
                transaction_id=transaction_id,
            )
            raise PaymentSagaError(
                "Falha durante a captura do pagamento."
            ) from exc

    async def cancel(
        self,
        transaction_id: UUID,
    ) -> Transaction:
        try:
            return await self.payment_service.cancel_payment(
                transaction_id=transaction_id,
            )
        except PaymentServiceError as exc:
            raise PaymentSagaError(
                "Falha durante o cancelamento do pagamento."
            ) from exc

    async def execute_with_capture(
        self,
        data: PaymentCreate,
    ) -> Transaction:
        """
        Executa pagamento que exige autorização seguida de captura.

        Fluxo:

        1. Criação/autorização
        2. Captura
        3. Compensação em caso de falha
        """

        transaction = await self._create_payment(data)

        if transaction.status == TransactionStatus.SUCCEEDED:
            return transaction

        if transaction.status != TransactionStatus.AUTHORIZED:
            raise PaymentSagaError(
                "O pagamento não alcançou o estado autorizado."
            )

        try:
            return await self.payment_service.capture_payment(
                transaction_id=transaction.id,
            )
        except PaymentServiceError as exc:
            await self._compensate_capture_failure(
                transaction_id=transaction.id,
            )

            raise PaymentSagaError(
                "A captura falhou e a compensação foi executada."
            ) from exc

    async def _create_payment(
        self,
        data: PaymentCreate,
    ) -> Transaction:
        try:
            return await self.payment_service.create_payment(data)
        except PaymentServiceError as exc:
            raise PaymentSagaError(
                "Não foi possível concluir a etapa de criação "
                "do pagamento."
            ) from exc

    async def _compensate_capture_failure(
        self,
        transaction_id: UUID,
    ) -> None:
        """
        Executa a compensação quando a captura falha.

        Caso o pagamento esteja autorizado, a ação compensatória
        consiste em cancelar a autorização no gateway.
        """

        try:
            transaction = await self.payment_service.get_payment(
                transaction_id
            )

            if transaction.status != TransactionStatus.AUTHORIZED:
                return

            await self.payment_service.cancel_payment(
                transaction_id
            )

        except PaymentServiceError as exc:
            raise PaymentSagaCompensationError(
                "Não foi possível compensar a autorização "
                "do pagamento."
            ) from exc


@dataclass(slots=True)
class PaymentSagaResult:
    """
    Resultado estruturado da execução da saga.

    Mantido separado da entidade Transaction para permitir
    evolução futura da comunicação baseada em eventos.
    """

    transaction_id: UUID
    status: TransactionStatus
    provider: PaymentProvider | None
    amount: Decimal
    compensated: bool = False
