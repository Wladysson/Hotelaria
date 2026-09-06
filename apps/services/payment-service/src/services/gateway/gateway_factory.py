from src.core.payment_gateway import PaymentGateway
from src.models.transactions import PaymentProvider
from src.services.gateway.paypal_gateway import PayPalGateway
from src.services.gateway.stripe_gateway import StripeGateway


class UnsupportedPaymentProviderError(Exception):
    """Indica que o provedor solicitado não é suportado."""


class GatewayFactory:
    def __init__(self) -> None:
        self._gateways: dict[PaymentProvider, PaymentGateway] = {
            PaymentProvider.STRIPE: StripeGateway(),
            PaymentProvider.PAYPAL: PayPalGateway(),
        }

    def get_gateway(
        self,
        provider: PaymentProvider | str | None,
    ) -> PaymentGateway:
        if provider is None:
            raise UnsupportedPaymentProviderError(
                "Nenhum provedor de pagamento foi informado."
            )

        if isinstance(provider, str):
            try:
                provider = PaymentProvider(provider.lower())
            except ValueError as exc:
                raise UnsupportedPaymentProviderError(
                    f"Provedor de pagamento não suportado: {provider}"
                ) from exc

        gateway = self._gateways.get(provider)

        if gateway is None:
            raise UnsupportedPaymentProviderError(
                f"Provedor de pagamento não suportado: {provider.value}"
            )

        return gateway

    def is_supported(
        self,
        provider: PaymentProvider | str | None,
    ) -> bool:
        try:
            self.get_gateway(provider)
            return True
        except UnsupportedPaymentProviderError:
            return False

    def supported_providers(self) -> list[str]:
        return [
            provider.value
            for provider in self._gateways
        ]