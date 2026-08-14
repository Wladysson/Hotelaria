from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from src.core.payment_gateway import (
    PaymentGatewayDeclinedError,
    PaymentGatewayError,
    PaymentGatewayTimeoutError,
)
from src.services.gateway.stripe_gateway import StripeGateway


@pytest.fixture
def stripe_gateway():
    return StripeGateway()


@pytest.fixture
def stripe_settings():
    with patch(
        "src.services.gateway.stripe_gateway.settings"
    ) as settings:
        settings.STRIPE_SECRET_KEY = "sk_test_123"
        settings.PAYMENT_TIMEOUT_SECONDS = 10
        yield settings


@pytest.mark.asyncio
async def test_provider_name(
    stripe_gateway,
):
    assert stripe_gateway.provider_name == "stripe"


@pytest.mark.asyncio
async def test_create_payment_success(
    stripe_gateway,
    stripe_settings,
):
    response_data = {
        "id": "pi_test_001",
        "status": "succeeded",
        "amount": 15000,
        "amount_received": 15000,
    }

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = response_data

    with patch(
        "httpx.AsyncClient.request",
        new_callable=AsyncMock,
        return_value=mock_response,
    ) as request_mock:
        result = await stripe_gateway.create_payment(
            transaction_id="transaction-001",
            amount=Decimal("150.00"),
            currency="BRL",
            payment_method="pm_test_001",
            description="Pagamento de reserva",
            metadata={
                "source": "test",
            },
        )

    assert result["id"] == "pi_test_001"
    assert result["gateway_transaction_id"] == "pi_test_001"
    assert result["status"] == "succeeded"
    assert result["captured_amount"] == Decimal("150.00")

    request_mock.assert_awaited_once()

    call_kwargs = request_mock.await_args.kwargs

    assert call_kwargs["method"] == "POST"
    assert call_kwargs["url"].endswith(
        "/payment_intents"
    )

    payload = call_kwargs["data"]

    assert payload["amount"] == 15000
    assert payload["currency"] == "brl"
    assert payload["payment_method"] == "pm_test_001"
    assert payload["confirm"] == "true"
    assert payload["description"] == "Pagamento de reserva"
    assert payload["metadata[source]"] == "test"
    assert payload["metadata[transaction_id]"] == "transaction-001"


@pytest.mark.asyncio
async def test_create_payment_requires_capture(
    stripe_gateway,
    stripe_settings,
):
    response_data = {
        "id": "pi_test_002",
        "status": "requires_capture",
        "amount": 15000,
        "amount_received": 0,
    }

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = response_data

    with patch(
        "httpx.AsyncClient.request",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        result = await stripe_gateway.create_payment(
            transaction_id="transaction-002",
            amount=Decimal("150.00"),
            currency="BRL",
            payment_method="pm_test_002",
        )

    assert result["status"] == "authorized"
    assert result["captured_amount"] == Decimal("0")


@pytest.mark.asyncio
async def test_create_payment_without_secret_key(
    stripe_gateway,
):
    with patch(
        "src.services.gateway.stripe_gateway.settings"
    ) as settings:
        settings.STRIPE_SECRET_KEY = None

        with pytest.raises(PaymentGatewayError) as exc_info:
            await stripe_gateway.create_payment(
                transaction_id="transaction-003",
                amount=Decimal("100.00"),
                currency="BRL",
                payment_method="pm_test_003",
            )

    assert "STRIPE_SECRET_KEY" in str(
        exc_info.value
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "gateway_status",
    [
        "canceled",
        "payment_failed",
    ],
)
async def test_create_payment_rejected_status(
    stripe_gateway,
    stripe_settings,
    gateway_status,
):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "pi_test_declined",
        "status": gateway_status,
    }

    with patch(
        "httpx.AsyncClient.request",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        with pytest.raises(
            PaymentGatewayDeclinedError
        ):
            await stripe_gateway.create_payment(
                transaction_id="transaction-declined",
                amount=Decimal("100.00"),
                currency="BRL",
                payment_method="pm_test_declined",
            )


@pytest.mark.asyncio
async def test_create_payment_processing_status(
    stripe_gateway,
    stripe_settings,
):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "pi_processing",
        "status": "requires_action",
        "amount_received": 0,
    }

    with patch(
        "httpx.AsyncClient.request",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        result = await stripe_gateway.create_payment(
            transaction_id="transaction-processing",
            amount=Decimal("100.00"),
            currency="BRL",
            payment_method="pm_processing",
        )

    assert result["status"] == "processing"


@pytest.mark.asyncio
async def test_capture_payment_success(
    stripe_gateway,
    stripe_settings,
):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "pi_capture_001",
        "status": "succeeded",
        "amount_received": 10000,
    }

    with patch(
        "httpx.AsyncClient.request",
        new_callable=AsyncMock,
        return_value=mock_response,
    ) as request_mock:
        result = await stripe_gateway.capture_payment(
            gateway_transaction_id="pi_capture_001",
            amount=Decimal("100.00"),
        )

    assert result["gateway_transaction_id"] == "pi_capture_001"
    assert result["status"] == "succeeded"
    assert result["captured_amount"] == Decimal("100.00")

    call_kwargs = request_mock.await_args.kwargs

    assert call_kwargs["method"] == "POST"
    assert call_kwargs["url"].endswith(
        "/payment_intents/pi_capture_001/capture"
    )
    assert call_kwargs["data"]["amount_to_capture"] == 10000


@pytest.mark.asyncio
async def test_capture_payment_without_amount(
    stripe_gateway,
    stripe_settings,
):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "pi_capture_002",
        "status": "succeeded",
        "amount_received": 15000,
    }

    with patch(
        "httpx.AsyncClient.request",
        new_callable=AsyncMock,
        return_value=mock_response,
    ) as request_mock:
        result = await stripe_gateway.capture_payment(
            gateway_transaction_id="pi_capture_002",
        )

    assert result["captured_amount"] == Decimal("150.00")

    call_kwargs = request_mock.await_args.kwargs

    assert call_kwargs["data"] == {}


@pytest.mark.asyncio
async def test_cancel_payment_success(
    stripe_gateway,
    stripe_settings,
):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "pi_cancel_001",
        "status": "canceled",
    }

    with patch(
        "httpx.AsyncClient.request",
        new_callable=AsyncMock,
        return_value=mock_response,
    ) as request_mock:
        result = await stripe_gateway.cancel_payment(
            gateway_transaction_id="pi_cancel_001",
        )

    assert result["gateway_transaction_id"] == "pi_cancel_001"
    assert result["status"] == "cancelled"

    call_kwargs = request_mock.await_args.kwargs

    assert call_kwargs["method"] == "POST"
    assert call_kwargs["url"].endswith(
        "/payment_intents/pi_cancel_001/cancel"
    )


@pytest.mark.asyncio
async def test_refund_payment_success(
    stripe_gateway,
    stripe_settings,
):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "re_test_001",
        "status": "succeeded",
    }

    with patch(
        "httpx.AsyncClient.request",
        new_callable=AsyncMock,
        return_value=mock_response,
    ) as request_mock:
        result = await stripe_gateway.refund_payment(
            gateway_transaction_id="pi_refund_001",
            amount=Decimal("50.00"),
            reason="customer_request",
        )

    assert result["id"] == "re_test_001"
    assert result["gateway_refund_id"] == "re_test_001"
    assert result["status"] == "succeeded"

    call_kwargs = request_mock.await_args.kwargs

    assert call_kwargs["method"] == "POST"
    assert call_kwargs["url"].endswith(
        "/refunds"
    )

    payload = call_kwargs["data"]

    assert payload["payment_intent"] == "pi_refund_001"
    assert payload["amount"] == 5000
    assert payload["metadata[reason]"] == "customer_request"


@pytest.mark.asyncio
async def test_refund_payment_without_amount(
    stripe_gateway,
    stripe_settings,
):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "re_test_002",
        "status": "succeeded",
    }

    with patch(
        "httpx.AsyncClient.request",
        new_callable=AsyncMock,
        return_value=mock_response,
    ) as request_mock:
        result = await stripe_gateway.refund_payment(
            gateway_transaction_id="pi_refund_002",
        )

    assert result["status"] == "succeeded"

    payload = request_mock.await_args.kwargs["data"]

    assert payload == {
        "payment_intent": "pi_refund_002",
    }


@pytest.mark.asyncio
async def test_get_payment_success(
    stripe_gateway,
    stripe_settings,
):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "pi_get_001",
        "status": "succeeded",
        "amount_received": 7500,
    }

    with patch(
        "httpx.AsyncClient.request",
        new_callable=AsyncMock,
        return_value=mock_response,
    ) as request_mock:
        result = await stripe_gateway.get_payment(
            gateway_transaction_id="pi_get_001",
        )

    assert result["id"] == "pi_get_001"
    assert result["gateway_transaction_id"] == "pi_get_001"
    assert result["status"] == "succeeded"
    assert result["captured_amount"] == Decimal("75.00")

    call_kwargs = request_mock.await_args.kwargs

    assert call_kwargs["method"] == "GET"
    assert call_kwargs["url"].endswith(
        "/payment_intents/pi_get_001"
    )


@pytest.mark.asyncio
async def test_request_handles_timeout(
    stripe_gateway,
    stripe_settings,
):
    with patch(
        "httpx.AsyncClient.request",
        new_callable=AsyncMock,
        side_effect=httpx.TimeoutException(
            "Timeout"
        ),
    ):
        with pytest.raises(
            PaymentGatewayTimeoutError
        ):
            await stripe_gateway.get_payment(
                gateway_transaction_id="pi_timeout",
            )


@pytest.mark.asyncio
async def test_request_handles_http_error(
    stripe_gateway,
    stripe_settings,
):
    with patch(
        "httpx.AsyncClient.request",
        new_callable=AsyncMock,
        side_effect=httpx.ConnectError(
            "Connection failed"
        ),
    ):
        with pytest.raises(
            PaymentGatewayError
        ):
            await stripe_gateway.get_payment(
                gateway_transaction_id="pi_connection_error",
            )


@pytest.mark.asyncio
async def test_request_handles_declined_http_status(
    stripe_gateway,
    stripe_settings,
):
    mock_response = Mock()
    mock_response.status_code = 402
    mock_response.json.return_value = {
        "error": {
            "message": "Your card was declined.",
        }
    }

    with patch(
        "httpx.AsyncClient.request",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        with pytest.raises(
            PaymentGatewayDeclinedError
        ) as exc_info:
            await stripe_gateway.get_payment(
                gateway_transaction_id="pi_declined",
            )

    assert "declined" in str(
        exc_info.value
    ).lower()


@pytest.mark.asyncio
async def test_request_handles_conflict_http_status(
    stripe_gateway,
    stripe_settings,
):
    mock_response = Mock()
    mock_response.status_code = 409
    mock_response.json.return_value = {
        "error": {
            "message": "Conflict.",
        }
    }

    with patch(
        "httpx.AsyncClient.request",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        with pytest.raises(
            PaymentGatewayDeclinedError
        ):
            await stripe_gateway.get_payment(
                gateway_transaction_id="pi_conflict",
            )


@pytest.mark.asyncio
async def test_request_handles_generic_http_error(
    stripe_gateway,
    stripe_settings,
):
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.json.return_value = {
        "error": {
            "message": "Internal Stripe error.",
        }
    }

    with patch(
        "httpx.AsyncClient.request",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        with pytest.raises(
            PaymentGatewayError
        ) as exc_info:
            await stripe_gateway.get_payment(
                gateway_transaction_id="pi_server_error",
            )

    assert "internal stripe error" in str(
        exc_info.value
    ).lower()


@pytest.mark.asyncio
async def test_request_uses_bearer_authentication(
    stripe_gateway,
    stripe_settings,
):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "pi_auth_001",
        "status": "succeeded",
        "amount_received": 10000,
    }

    with patch(
        "httpx.AsyncClient.request",
        new_callable=AsyncMock,
        return_value=mock_response,
    ) as request_mock:
        await stripe_gateway.get_payment(
            gateway_transaction_id="pi_auth_001",
        )

    headers = request_mock.await_args.kwargs["headers"]

    assert headers["Authorization"] == (
        "Bearer sk_test_123"
    )

    assert headers["Content-Type"] == (
        "application/x-www-form-urlencoded"
    )


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        (Decimal("100.00"), 10000),
        (Decimal("150.50"), 15050),
        (Decimal("0.01"), 1),
        (Decimal("999.99"), 99999),
    ],
)
def test_to_minor_units(
    amount,
    expected,
):
    assert StripeGateway._to_minor_units(
        amount
    ) == expected


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        (10000, Decimal("100")),
        (15050, Decimal("150.5")),
        (1, Decimal("0.01")),
        (99999, Decimal("999.99")),
    ],
)
def test_from_minor_units(
    amount,
    expected,
):
    assert StripeGateway._from_minor_units(
        amount
    ) == expected


def test_extract_error_from_stripe_response():
    response = Mock()

    response.json.return_value = {
        "error": {
            "message": "Cartão recusado.",
        }
    }

    result = StripeGateway._extract_error(
        response
    )

    assert result == "Cartão recusado."


def test_extract_error_without_message():
    response = Mock()

    response.json.return_value = {
        "error": {}
    }

    result = StripeGateway._extract_error(
        response
    )

    assert result == "Erro retornado pelo Stripe."


def test_extract_error_with_invalid_json():
    response = Mock()

    response.json.side_effect = ValueError()

    result = StripeGateway._extract_error(
        response
    )

    assert result == "Erro retornado pelo Stripe."