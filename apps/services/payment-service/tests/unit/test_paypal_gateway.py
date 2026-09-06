from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from src.core.payment_gateway import (
    PaymentGatewayDeclinedError,
    PaymentGatewayError,
    PaymentGatewayTimeoutError,
)
from src.services.gateway.paypal_gateway import PayPalGateway


@pytest.fixture
def paypal_gateway():
    return PayPalGateway()


@pytest.fixture
def paypal_settings():
    with patch(
        "src.services.gateway.paypal_gateway.settings"
    ) as settings:
        settings.PAYPAL_CLIENT_ID = "client-test-123"
        settings.PAYPAL_CLIENT_SECRET = "secret-test-123"
        settings.PAYPAL_BASE_URL = "https://api-m.sandbox.paypal.com"
        settings.PAYMENT_TIMEOUT_SECONDS = 10
        yield settings


@pytest.mark.asyncio
async def test_provider_name(
    paypal_gateway,
):
    assert paypal_gateway.provider_name == "paypal"


@pytest.mark.asyncio
async def test_create_payment_success(
    paypal_gateway,
    paypal_settings,
):
    token_response = Mock()
    token_response.status_code = 200
    token_response.json.return_value = {
        "access_token": "access-token-test",
    }

    order_response = Mock()
    order_response.status_code = 201
    order_response.content = b'{"id":"ORDER-001","status":"CREATED"}'
    order_response.json.return_value = {
        "id": "ORDER-001",
        "status": "CREATED",
    }

    with patch(
        "httpx.AsyncClient.post",
        new_callable=AsyncMock,
        return_value=token_response,
    ) as token_mock:
        with patch(
            "httpx.AsyncClient.request",
            new_callable=AsyncMock,
            return_value=order_response,
        ) as request_mock:
            result = await paypal_gateway.create_payment(
                transaction_id="transaction-001",
                amount=Decimal("150.00"),
                currency="BRL",
                payment_method="payment-method-001",
                description="Pagamento de reserva",
                metadata={
                    "source": "unit-test",
                },
            )

    assert result["id"] == "ORDER-001"
    assert result["gateway_transaction_id"] == "ORDER-001"
    assert result["status"] == "processing"
    assert result["captured_amount"] == Decimal("0.00")

    token_mock.assert_awaited_once()

    request_mock.assert_awaited_once()

    call_kwargs = request_mock.await_args.kwargs

    assert call_kwargs["method"] == "POST"
    assert call_kwargs["url"].endswith(
        "/v2/checkout/orders"
    )

    headers = call_kwargs["headers"]

    assert headers["Authorization"] == (
        "Bearer access-token-test"
    )

    payload = call_kwargs["json"]

    assert payload["intent"] == "CAPTURE"

    purchase_unit = payload["purchase_units"][0]

    assert purchase_unit["reference_id"] == (
        "transaction-001"
    )

    assert purchase_unit["amount"]["currency_code"] == "BRL"
    assert purchase_unit["amount"]["value"] == "150.00"
    assert purchase_unit["description"] == (
        "Pagamento de reserva"
    )


@pytest.mark.asyncio
async def test_create_payment_completed_status(
    paypal_gateway,
    paypal_settings,
):
    token_response = Mock()
    token_response.status_code = 200
    token_response.json.return_value = {
        "access_token": "access-token-test",
    }

    order_response = Mock()
    order_response.status_code = 201
    order_response.content = b'{"id":"ORDER-002","status":"COMPLETED"}'
    order_response.json.return_value = {
        "id": "ORDER-002",
        "status": "COMPLETED",
    }

    with patch(
        "httpx.AsyncClient.post",
        new_callable=AsyncMock,
        return_value=token_response,
    ):
        with patch(
            "httpx.AsyncClient.request",
            new_callable=AsyncMock,
            return_value=order_response,
        ):
            result = await paypal_gateway.create_payment(
                transaction_id="transaction-002",
                amount=Decimal("200.00"),
                currency="BRL",
                payment_method="payment-method-002",
            )

    assert result["status"] == "succeeded"
    assert result["captured_amount"] == Decimal("200.00")


@pytest.mark.asyncio
async def test_create_payment_without_client_id(
    paypal_gateway,
):
    with patch(
        "src.services.gateway.paypal_gateway.settings"
    ) as settings:
        settings.PAYPAL_CLIENT_ID = None
        settings.PAYPAL_CLIENT_SECRET = "secret"

        with pytest.raises(
            PaymentGatewayError
        ) as exc_info:
            await paypal_gateway.create_payment(
                transaction_id="transaction-003",
                amount=Decimal("100.00"),
                currency="BRL",
                payment_method="payment-method-003",
            )

    assert "PAYPAL_CLIENT_ID" in str(
        exc_info.value
    )


@pytest.mark.asyncio
async def test_create_payment_without_client_secret(
    paypal_gateway,
):
    with patch(
        "src.services.gateway.paypal_gateway.settings"
    ) as settings:
        settings.PAYPAL_CLIENT_ID = "client"
        settings.PAYPAL_CLIENT_SECRET = None

        with pytest.raises(
            PaymentGatewayError
        ) as exc_info:
            await paypal_gateway.create_payment(
                transaction_id="transaction-004",
                amount=Decimal("100.00"),
                currency="BRL",
                payment_method="payment-method-004",
            )

    assert "PAYPAL_CLIENT_SECRET" in str(
        exc_info.value
    )


@pytest.mark.asyncio
async def test_capture_payment_success(
    paypal_gateway,
    paypal_settings,
):
    token_response = Mock()
    token_response.status_code = 200
    token_response.json.return_value = {
        "access_token": "access-token-test",
    }

    capture_response = Mock()
    capture_response.status_code = 201
    capture_response.content = b'{"status":"COMPLETED"}'
    capture_response.json.return_value = {
        "status": "COMPLETED",
        "purchase_units": [
            {
                "payments": {
                    "captures": [
                        {
                            "id": "CAPTURE-001",
                            "status": "COMPLETED",
                            "amount": {
                                "currency_code": "BRL",
                                "value": "150.00",
                            },
                        }
                    ]
                }
            }
        ],
    }

    with patch(
        "httpx.AsyncClient.post",
        new_callable=AsyncMock,
        return_value=token_response,
    ):
        with patch(
            "httpx.AsyncClient.request",
            new_callable=AsyncMock,
            return_value=capture_response,
        ) as request_mock:
            result = await paypal_gateway.capture_payment(
                gateway_transaction_id="ORDER-003",
                amount=Decimal("150.00"),
            )

    assert result["status"] == "succeeded"
    assert result["captured_amount"] == Decimal("150.00")
    assert result["gateway_transaction_id"] == "ORDER-003"

    call_kwargs = request_mock.await_args.kwargs

    assert call_kwargs["method"] == "POST"
    assert call_kwargs["url"].endswith(
        "/v2/checkout/orders/ORDER-003/capture"
    )


@pytest.mark.asyncio
async def test_capture_payment_uses_requested_amount_when_gateway_returns_zero(
    paypal_gateway,
    paypal_settings,
):
    token_response = Mock()
    token_response.status_code = 200
    token_response.json.return_value = {
        "access_token": "access-token-test",
    }

    capture_response = Mock()
    capture_response.status_code = 201
    capture_response.content = b'{"status":"COMPLETED"}'
    capture_response.json.return_value = {
        "status": "COMPLETED",
        "purchase_units": [],
    }

    with patch(
        "httpx.AsyncClient.post",
        new_callable=AsyncMock,
        return_value=token_response,
    ):
        with patch(
            "httpx.AsyncClient.request",
            new_callable=AsyncMock,
            return_value=capture_response,
        ):
            result = await paypal_gateway.capture_payment(
                gateway_transaction_id="ORDER-004",
                amount=Decimal("125.00"),
            )

    assert result["captured_amount"] == Decimal("125.00")


@pytest.mark.asyncio
async def test_capture_payment_rejects_incomplete_capture(
    paypal_gateway,
    paypal_settings,
):
    token_response = Mock()
    token_response.status_code = 200
    token_response.json.return_value = {
        "access_token": "access-token-test",
    }

    capture_response = Mock()
    capture_response.status_code = 201
    capture_response.content = b'{"status":"PENDING"}'
    capture_response.json.return_value = {
        "status": "PENDING",
    }

    with patch(
        "httpx.AsyncClient.post",
        new_callable=AsyncMock,
        return_value=token_response,
    ):
        with patch(
            "httpx.AsyncClient.request",
            new_callable=AsyncMock,
            return_value=capture_response,
        ):
            with pytest.raises(
                PaymentGatewayError
            ):
                await paypal_gateway.capture_payment(
                    gateway_transaction_id="ORDER-005",
                )


@pytest.mark.asyncio
async def test_cancel_payment_is_not_supported(
    paypal_gateway,
):
    with pytest.raises(
        PaymentGatewayError
    ) as exc_info:
        await paypal_gateway.cancel_payment(
            gateway_transaction_id="ORDER-006",
        )

    assert "cancelamento" in str(
        exc_info.value
    ).lower()


@pytest.mark.asyncio
async def test_refund_payment_success(
    paypal_gateway,
    paypal_settings,
):
    token_response = Mock()
    token_response.status_code = 200
    token_response.json.return_value = {
        "access_token": "access-token-test",
    }

    refund_response = Mock()
    refund_response.status_code = 201
    refund_response.content = b'{"id":"REFUND-001","status":"COMPLETED"}'
    refund_response.json.return_value = {
        "id": "REFUND-001",
        "status": "COMPLETED",
    }

    with patch(
        "httpx.AsyncClient.post",
        new_callable=AsyncMock,
        return_value=token_response,
    ):
        with patch(
            "httpx.AsyncClient.request",
            new_callable=AsyncMock,
            return_value=refund_response,
        ) as request_mock:
            result = await paypal_gateway.refund_payment(
                gateway_transaction_id="CAPTURE-001",
                amount=Decimal("50.00"),
                reason="customer_request",
            )

    assert result["id"] == "REFUND-001"
    assert result["gateway_refund_id"] == "REFUND-001"
    assert result["status"] == "succeeded"

    call_kwargs = request_mock.await_args.kwargs

    assert call_kwargs["method"] == "POST"
    assert call_kwargs["url"].endswith(
        "/v2/payments/captures/CAPTURE-001/refund"
    )

    payload = call_kwargs["json"]

    assert payload["amount"]["value"] == "50.00"
    assert payload["amount"]["currency_code"] == "BRL"
    assert payload["note_to_payer"] == "customer_request"


@pytest.mark.asyncio
async def test_refund_payment_without_amount(
    paypal_gateway,
    paypal_settings,
):
    token_response = Mock()
    token_response.status_code = 200
    token_response.json.return_value = {
        "access_token": "access-token-test",
    }

    refund_response = Mock()
    refund_response.status_code = 201
    refund_response.content = b'{"id":"REFUND-002","status":"COMPLETED"}'
    refund_response.json.return_value = {
        "id": "REFUND-002",
        "status": "COMPLETED",
    }

    with patch(
        "httpx.AsyncClient.post",
        new_callable=AsyncMock,
        return_value=token_response,
    ):
        with patch(
            "httpx.AsyncClient.request",
            new_callable=AsyncMock,
            return_value=refund_response,
        ) as request_mock:
            result = await paypal_gateway.refund_payment(
                gateway_transaction_id="CAPTURE-002",
            )

    assert result["status"] == "succeeded"

    payload = request_mock.await_args.kwargs["json"]

    assert payload == {}


@pytest.mark.asyncio
async def test_get_payment_success(
    paypal_gateway,
    paypal_settings,
):
    token_response = Mock()
    token_response.status_code = 200
    token_response.json.return_value = {
        "access_token": "access-token-test",
    }

    order_response = Mock()
    order_response.status_code = 200
    order_response.content = b'{"id":"ORDER-007","status":"COMPLETED"}'
    order_response.json.return_value = {
        "id": "ORDER-007",
        "status": "COMPLETED",
    }

    with patch(
        "httpx.AsyncClient.post",
        new_callable=AsyncMock,
        return_value=token_response,
    ):
        with patch(
            "httpx.AsyncClient.request",
            new_callable=AsyncMock,
            return_value=order_response,
        ) as request_mock:
            result = await paypal_gateway.get_payment(
                gateway_transaction_id="ORDER-007",
            )

    assert result["id"] == "ORDER-007"
    assert result["gateway_transaction_id"] == "ORDER-007"
    assert result["status"] == "COMPLETED"

    call_kwargs = request_mock.await_args.kwargs

    assert call_kwargs["method"] == "GET"
    assert call_kwargs["url"].endswith(
        "/v2/checkout/orders/ORDER-007"
    )


@pytest.mark.asyncio
async def test_get_access_token_success(
    paypal_gateway,
    paypal_settings,
):
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "access_token": "oauth-token",
    }

    with patch(
        "httpx.AsyncClient.post",
        new_callable=AsyncMock,
        return_value=response,
    ) as request_mock:
        token = await paypal_gateway._get_access_token()

    assert token == "oauth-token"

    call_kwargs = request_mock.await_args.kwargs

    assert call_kwargs["url"].endswith(
        "/v1/oauth2/token"
    )

    assert call_kwargs["data"] == {
        "grant_type": "client_credentials",
    }

    assert call_kwargs["headers"]["Content-Type"] == (
        "application/x-www-form-urlencoded"
    )


@pytest.mark.asyncio
async def test_get_access_token_handles_timeout(
    paypal_gateway,
    paypal_settings,
):
    with patch(
        "httpx.AsyncClient.post",
        new_callable=AsyncMock,
        side_effect=httpx.TimeoutException(
            "Timeout"
        ),
    ):
        with pytest.raises(
            PaymentGatewayTimeoutError
        ):
            await paypal_gateway._get_access_token()


@pytest.mark.asyncio
async def test_get_access_token_handles_http_error(
    paypal_gateway,
    paypal_settings,
):
    with patch(
        "httpx.AsyncClient.post",
        new_callable=AsyncMock,
        side_effect=httpx.ConnectError(
            "Connection failed"
        ),
    ):
        with pytest.raises(
            PaymentGatewayError
        ):
            await paypal_gateway._get_access_token()


@pytest.mark.asyncio
async def test_get_access_token_rejects_http_error_response(
    paypal_gateway,
    paypal_settings,
):
    response = Mock()
    response.status_code = 401

    with patch(
        "httpx.AsyncClient.post",
        new_callable=AsyncMock,
        return_value=response,
    ):
        with pytest.raises(
            PaymentGatewayError
        ):
            await paypal_gateway._get_access_token()


@pytest.mark.asyncio
async def test_get_access_token_requires_token_in_response(
    paypal_gateway,
    paypal_settings,
):
    response = Mock()
    response.status_code = 200
    response.json.return_value = {}

    with patch(
        "httpx.AsyncClient.post",
        new_callable=AsyncMock,
        return_value=response,
    ):
        with pytest.raises(
            PaymentGatewayError
        ) as exc_info:
            await paypal_gateway._get_access_token()

    assert "token" in str(
        exc_info.value
    ).lower()


@pytest.mark.asyncio
async def test_request_handles_timeout(
    paypal_gateway,
    paypal_settings,
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
            await paypal_gateway._request(
                method="GET",
                endpoint="/test",
                access_token="token",
            )


@pytest.mark.asyncio
async def test_request_handles_connection_error(
    paypal_gateway,
    paypal_settings,
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
            await paypal_gateway._request(
                method="GET",
                endpoint="/test",
                access_token="token",
            )


@pytest.mark.asyncio
async def test_request_handles_declined_status(
    paypal_gateway,
    paypal_settings,
):
    response = Mock()
    response.status_code = 400
    response.json.return_value = {
        "name": "INVALID_REQUEST",
        "message": "Invalid payment request.",
    }

    with patch(
        "httpx.AsyncClient.request",
        new_callable=AsyncMock,
        return_value=response,
    ):
        with pytest.raises(
            PaymentGatewayDeclinedError
        ) as exc_info:
            await paypal_gateway._request(
                method="POST",
                endpoint="/test",
                access_token="token",
                json={},
            )

    assert "invalid payment request" in str(
        exc_info.value
    ).lower()


@pytest.mark.asyncio
async def test_request_handles_unprocessable_status(
    paypal_gateway,
    paypal_settings,
):
    response = Mock()
    response.status_code = 422
    response.json.return_value = {
        "name": "UNPROCESSABLE_ENTITY",
        "message": "Invalid entity.",
    }

    with patch(
        "httpx.AsyncClient.request",
        new_callable=AsyncMock,
        return_value=response,
    ):
        with pytest.raises(
            PaymentGatewayDeclinedError
        ):
            await paypal_gateway._request(
                method="POST",
                endpoint="/test",
                access_token="token",
                json={},
            )


@pytest.mark.asyncio
async def test_request_handles_generic_http_error(
    paypal_gateway,
    paypal_settings,
):
    response = Mock()
    response.status_code = 500
    response.json.return_value = {
        "name": "INTERNAL_ERROR",
        "message": "Internal server error.",
    }

    with patch(
        "httpx.AsyncClient.request",
        new_callable=AsyncMock,
        return_value=response,
    ):
        with pytest.raises(
            PaymentGatewayError
        ) as exc_info:
            await paypal_gateway._request(
                method="GET",
                endpoint="/test",
                access_token="token",
            )

    assert "internal server error" in str(
        exc_info.value
    ).lower()


@pytest.mark.asyncio
async def test_request_returns_empty_dict_for_empty_response(
    paypal_gateway,
    paypal_settings,
):
    response = Mock()
    response.status_code = 204
    response.content = b""

    with patch(
        "httpx.AsyncClient.request",
        new_callable=AsyncMock,
        return_value=response,
    ):
        result = await paypal_gateway._request(
            method="POST",
            endpoint="/test",
            access_token="token",
        )

    assert result == {}


def test_extract_captured_amount():
    response = {
        "purchase_units": [
            {
                "payments": {
                    "captures": [
                        {
                            "amount": {
                                "value": "100.00",
                            }
                        },
                        {
                            "amount": {
                                "value": "50.50",
                            }
                        },
                    ]
                }
            }
        ]
    }

    result = PayPalGateway._extract_captured_amount(
        response
    )

    assert result == Decimal("150.50")


def test_extract_captured_amount_without_captures():
    response = {
        "purchase_units": [
            {
                "payments": {
                    "captures": []
                }
            }
        ]
    }

    result = PayPalGateway._extract_captured_amount(
        response
    )

    assert result == Decimal("0.00")


def test_extract_error_from_paypal_response():
    response = Mock()

    response.json.return_value = {
        "name": "INVALID_REQUEST",
        "message": "Invalid request.",
    }

    result = PayPalGateway._extract_error(
        response
    )

    assert result == "Invalid request."


def test_extract_error_uses_name_when_message_is_missing():
    response = Mock()

    response.json.return_value = {
        "name": "INVALID_REQUEST",
    }

    result = PayPalGateway._extract_error(
        response
    )

    assert result == "INVALID_REQUEST"


def test_extract_error_with_invalid_json():
    response = Mock()

    response.json.side_effect = ValueError()

    result = PayPalGateway._extract_error(
        response
    )

    assert result == "Erro retornado pelo PayPal."