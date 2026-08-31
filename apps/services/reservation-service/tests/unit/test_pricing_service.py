from decimal import Decimal

import pytest

from src.services.pricing_service import PricingService


@pytest.fixture
def pricing_service():
    return PricingService()


def test_service_must_be_created(
    pricing_service,
):
    assert pricing_service is not None


def test_calculated_price_must_be_decimal(
    pricing_service,
):
    if hasattr(pricing_service, "calculate"):
        result = pricing_service.calculate(
            Decimal("100.00"),
            2,
        )

        assert isinstance(result, Decimal)