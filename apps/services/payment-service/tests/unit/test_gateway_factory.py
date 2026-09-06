from unittest.mock import patch

import pytest

from src.models.transactions import PaymentProvider
from src.services.gateway.gateway_factory import (
    GatewayFactory,
    UnsupportedPaymentProviderError,
)
from src.services.gateway.paypal_gateway import PayPalGateway
from src.services.gateway.stripe_gateway import StripeGateway


@pytest.fixture
def gateway_factory():
    return GatewayFactory()


def test_factory_registers_stripe_gateway(
    gateway_factory,
):
    gateway = gateway_factory.get_gateway(
        PaymentProvider.STRIPE,
    )

    assert isinstance(
        gateway,
        StripeGateway,
    )

    assert gateway.provider_name == "stripe"


def test_factory_registers_paypal_gateway(
    gateway_factory,
):
    gateway = gateway_factory.get_gateway(
        PaymentProvider.PAYPAL,
    )

    assert isinstance(
        gateway,
        PayPalGateway,
    )

    assert gateway.provider_name == "paypal"


def test_get_gateway_accepts_provider_string(
    gateway_factory,
):
    gateway = gateway_factory.get_gateway(
        "stripe",
    )

    assert isinstance(
        gateway,
        StripeGateway,
    )


def test_get_gateway_normalizes_uppercase_provider(
    gateway_factory,
):
    gateway = gateway_factory.get_gateway(
        "STRIPE",
    )

    assert isinstance(
        gateway,
        StripeGateway,
    )


def test_get_gateway_normalizes_paypal_provider(
    gateway_factory,
):
    gateway = gateway_factory.get_gateway(
        "PAYPAL",
    )

    assert isinstance(
        gateway,
        PayPalGateway,
    )


def test_get_gateway_rejects_none(
    gateway_factory,
):
    with pytest.raises(
        UnsupportedPaymentProviderError,
    ) as exc_info:
        gateway_factory.get_gateway(None)

    assert "nenhum provedor" in str(
        exc_info.value
    ).lower()


@pytest.mark.parametrize(
    "provider",
    [
        "mercadopago",
        "adyen",
        "unknown",
        "",
        "stripe-invalid",
    ],
)
def test_get_gateway_rejects_unsupported_provider(
    gateway_factory,
    provider,
):
    with pytest.raises(
        UnsupportedPaymentProviderError,
    ):
        gateway_factory.get_gateway(provider)


def test_get_gateway_rejects_invalid_enum_value(
    gateway_factory,
):
    with pytest.raises(
        UnsupportedPaymentProviderError,
    ):
        gateway_factory.get_gateway(
            "invalid-provider",
        )


def test_is_supported_returns_true_for_stripe(
    gateway_factory,
):
    assert gateway_factory.is_supported(
        PaymentProvider.STRIPE
    ) is True


def test_is_supported_returns_true_for_paypal(
    gateway_factory,
):
    assert gateway_factory.is_supported(
        PaymentProvider.PAYPAL
    ) is True


def test_is_supported_returns_true_for_string(
    gateway_factory,
):
    assert gateway_factory.is_supported(
        "stripe"
    ) is True


def test_is_supported_returns_false_for_unknown_provider(
    gateway_factory,
):
    assert gateway_factory.is_supported(
        "unknown"
    ) is False


def test_is_supported_returns_false_for_none(
    gateway_factory,
):
    assert gateway_factory.is_supported(
        None
    ) is False


def test_supported_providers_contains_stripe_and_paypal(
    gateway_factory,
):
    providers = gateway_factory.supported_providers()

    assert "stripe" in providers
    assert "paypal" in providers


def test_supported_providers_returns_only_registered_providers(
    gateway_factory,
):
    providers = gateway_factory.supported_providers()

    assert set(providers) == {
        "stripe",
        "paypal",
    }


def test_factory_returns_same_stripe_instance(
    gateway_factory,
):
    first_gateway = gateway_factory.get_gateway(
        PaymentProvider.STRIPE,
    )

    second_gateway = gateway_factory.get_gateway(
        PaymentProvider.STRIPE,
    )

    assert first_gateway is second_gateway


def test_factory_returns_same_paypal_instance(
    gateway_factory,
):
    first_gateway = gateway_factory.get_gateway(
        PaymentProvider.PAYPAL,
    )

    second_gateway = gateway_factory.get_gateway(
        PaymentProvider.PAYPAL,
    )

    assert first_gateway is second_gateway


def test_factory_keeps_gateway_implementations_isolated(
    gateway_factory,
):
    stripe_gateway = gateway_factory.get_gateway(
        PaymentProvider.STRIPE,
    )

    paypal_gateway = gateway_factory.get_gateway(
        PaymentProvider.PAYPAL,
    )

    assert stripe_gateway is not paypal_gateway
    assert stripe_gateway.provider_name != paypal_gateway.provider_name


def test_factory_converts_provider_enum_correctly(
    gateway_factory,
):
    with patch.object(
        gateway_factory,
        "_gateways",
        gateway_factory._gateways.copy(),
    ):
        gateway = gateway_factory.get_gateway(
            PaymentProvider.STRIPE,
        )

    assert gateway.provider_name == "stripe"