from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any


class PaymentGatewayError(Exception):
    """Erro base para falhas de comunicação com gateways de pagamento."""


class PaymentGatewayTimeoutError(PaymentGatewayError):
    """Erro gerado quando o gateway excede o tempo limite."""


class PaymentGatewayDeclinedError(PaymentGatewayError):
    """Erro gerado quando o gateway recusa uma transação."""


class PaymentGateway(ABC):
    """
    Contrato para implementação de gateways de pagamento.

    Cada provedor externo deve implementar esta interface,
    mantendo o domínio independente da implementação específica.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Retorna o identificador do provedor."""
        raise NotImplementedError

    @abstractmethod
    async def create_payment(
        self,
        *,
        transaction_id: str,
        amount: Decimal,
        currency: str,
        payment_method: str,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Cria uma operação de pagamento no gateway externo.

        Retorna os dados normalizados da operação para o
        serviço de pagamentos.
        """
        raise NotImplementedError

    @abstractmethod
    async def capture_payment(
        self,
        *,
        gateway_transaction_id: str,
        amount: Decimal | None = None,
    ) -> dict[str, Any]:
        """Captura um pagamento previamente autorizado."""
        raise NotImplementedError

    @abstractmethod
    async def cancel_payment(
        self,
        *,
        gateway_transaction_id: str,
    ) -> dict[str, Any]:
        """Cancela uma operação de pagamento."""
        raise NotImplementedError

    @abstractmethod
    async def refund_payment(
        self,
        *,
        gateway_transaction_id: str,
        amount: Decimal | None = None,
        reason: str | None = None,
    ) -> dict[str, Any]:
        """Solicita o reembolso de um pagamento."""
        raise NotImplementedError

    @abstractmethod
    async def get_payment(
        self,
        *,
        gateway_transaction_id: str,
    ) -> dict[str, Any]:
        """Consulta o estado de uma transação no gateway."""
        raise NotImplementedError