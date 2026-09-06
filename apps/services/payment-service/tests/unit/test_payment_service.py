from decimal import Decimal
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from src.core.payment_gateway import (
    PaymentGatewayDeclinedError,
    PaymentGatewayError,
    PaymentGatewayTimeoutError,
)
from src.models.payment_method import (
    PaymentMethod,
    PaymentMethodStatus,
    PaymentMethodType,
)
from src.models.transactions import (
    PaymentProvider,
    TransactionStatus,
)
from src.schemas.payment import PaymentCreate
from src.services.payment_service import (
    InvalidTransactionStateError,
    PaymentAlreadyProcessedError,
    PaymentMethodNotFoundError,
    PaymentService,
    PaymentServiceError,
    TransactionNotFoundError,
)


@pytest.fixture
def payment_service(db_session):
    gateway_factory = Mock()
    return PaymentService(
        session=db_session,
        gateway_factory=gateway_factory,
    )


@pytest.fixture
def payment_data(
    fake_reservation_id,
    fake_customer_id,
    fake_payment_method_id,
):
    return PaymentCreate(
        reservation_id=fake_reservation_id,
        customer_id=fake_customer_id,
        amount=Decimal("150.00"),
        currency="BRL",
        payment_method_id=fake_payment_method_id,
        provider=PaymentProvider.STRIPE,
        description="Pagamento de reserva",
        requires_capture=False,
        idempotency_key=f"payment-{uuid4()}",
        metadata={"source": "unit-test"},
    )


@pytest.fixture
async def active_payment_method(
    db_session,
    fake_customer_id,
    fake_payment_method_id,
):
    payment_method = PaymentMethod(
        id=fake_payment_method_id,
        customer_id=fake_customer_id,
        method_type=PaymentMethodType.CREDIT_CARD,
        status=PaymentMethodStatus.ACTIVE,
        provider="stripe",
        provider_method_id="pm_test_001",
        card_brand="visa",
        card_last_four="4242",
        is_default=True,
    )

    db_session.add(payment_method)
    await db_session.flush()
    await db_session.refresh(payment_method)

    return payment_method


@pytest.mark.asyncio
async def test_create_payment_success(
    payment_service,
    payment_data,
    active_payment_method,
    mock_gateway_response,
):
    gateway = Mock()
    gateway.create_payment = AsyncMock(
        return_value=mock_gateway_response,
    )

    payment_service.gateway_factory.get_gateway.return_value = gateway

    transaction = await payment_service.create_payment(payment_data)

    assert transaction.id is not None
    assert transaction.reservation_id == payment_data.reservation_id
    assert transaction.customer_id == payment_data.customer_id
    assert transaction.amount == Decimal("150.00")
    assert transaction.currency == "BRL"
    assert transaction.provider == PaymentProvider.STRIPE
    assert transaction.status == TransactionStatus.SUCCEEDED
    assert transaction.gateway_transaction_id == "gateway-tx-test-001"
    assert transaction.captured_amount == Decimal("150.00")

    gateway.create_payment.assert_awaited_once_with(
        transaction_id=str(transaction.id),
        amount=payment_data.amount,
        currency="BRL",
        payment_method=str(payment_data.payment_method_id),
        description=payment_data.description,
        metadata=payment_data.metadata,
    )


@pytest.mark.asyncio
async def test_create_payment_requires_capture(
    payment_service,
    payment_data,
    active_payment_method,
):
    payment_data.requires_capture = True

    gateway = Mock()
    gateway.create_payment = AsyncMock(
        return_value={
            "id": "gateway-tx-002",
            "gateway_transaction_id": "gateway-tx-002",
            "status": "authorized",
            "captured_amount": Decimal("0.00"),
        },
    )

    payment_service.gateway_factory.get_gateway.return_value = gateway

    transaction = await payment_service.create_payment(payment_data)

    assert transaction.status == TransactionStatus.AUTHORIZED
    assert transaction.requires_capture is True
    assert transaction.captured_amount == Decimal("0.00")


@pytest.mark.asyncio
async def test_create_payment_rejects_duplicate_idempotency_key(
    payment_service,
    payment_data,
    active_payment_method,
):
    existing_transaction = Mock()

    payment_service.transaction_repository.get_by_idempotency_key = (
        AsyncMock(return_value=existing_transaction)
    )

    with pytest.raises(PaymentAlreadyProcessedError):
        await payment_service.create_payment(payment_data)

    payment_service.transaction_repository.get_by_idempotency_key.assert_awaited_once_with(
        payment_data.idempotency_key
    )

    payment_service.gateway_factory.get_gateway.assert_not_called()


@pytest.mark.asyncio
async def test_create_payment_requires_existing_payment_method(
    payment_service,
    payment_data,
):
    payment_service.payment_method_repository.get_by_id = AsyncMock(
        return_value=None,
    )

    with pytest.raises(PaymentMethodNotFoundError):
        await payment_service.create_payment(payment_data)

    payment_service.gateway_factory.get_gateway.assert_not_called()


@pytest.mark.asyncio
async def test_create_payment_handles_gateway_declined(
    payment_service,
    payment_data,
    active_payment_method,
):
    gateway = Mock()
    gateway.create_payment = AsyncMock(
        side_effect=PaymentGatewayDeclinedError(
            "Pagamento recusado."
        ),
    )

    payment_service.gateway_factory.get_gateway.return_value = gateway

    with pytest.raises(PaymentServiceError) as exc_info:
        await payment_service.create_payment(payment_data)

    assert "recusado" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_create_payment_handles_gateway_timeout(
    payment_service,
    payment_data,
    active_payment_method,
):
    gateway = Mock()
    gateway.create_payment = AsyncMock(
        side_effect=PaymentGatewayTimeoutError(
            "Timeout no gateway."
        ),
    )

    payment_service.gateway_factory.get_gateway.return_value = gateway

    with pytest.raises(PaymentServiceError) as exc_info:
        await payment_service.create_payment(payment_data)

    assert "tempo limite" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_create_payment_handles_gateway_error(
    payment_service,
    payment_data,
    active_payment_method,
):
    gateway = Mock()
    gateway.create_payment = AsyncMock(
        side_effect=PaymentGatewayError(
            "Falha de comunicação."
        ),
    )

    payment_service.gateway_factory.get_gateway.return_value = gateway

    with pytest.raises(PaymentServiceError) as exc_info:
        await payment_service.create_payment(payment_data)

    assert "falha" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_get_payment_success(
    payment_service,
):
    transaction = Mock()

    payment_service.transaction_repository.get_by_id = AsyncMock(
        return_value=transaction,
    )

    transaction_id = uuid4()

    result = await payment_service.get_payment(transaction_id)

    assert result is transaction

    payment_service.transaction_repository.get_by_id.assert_awaited_once_with(
        transaction_id
    )


@pytest.mark.asyncio
async def test_get_payment_not_found(
    payment_service,
):
    transaction_id = uuid4()

    payment_service.transaction_repository.get_by_id = AsyncMock(
        return_value=None,
    )

    with pytest.raises(TransactionNotFoundError):
        await payment_service.get_payment(transaction_id)


@pytest.mark.asyncio
async def test_capture_payment_success(
    payment_service,
):
    transaction = Mock()
    transaction.id = uuid4()
    transaction.status = TransactionStatus.AUTHORIZED
    transaction.gateway_transaction_id = "gateway-tx-003"
    transaction.provider = PaymentProvider.STRIPE
    transaction.amount = Decimal("150.00")
    transaction.captured_amount = Decimal("0.00")

    payment_service.transaction_repository.get_by_id = AsyncMock(
        return_value=transaction,
    )
    payment_service.transaction_repository.update = AsyncMock(
        return_value=transaction,
    )

    gateway = Mock()
    gateway.capture_payment = AsyncMock(
        return_value={
            "id": "gateway-tx-003",
            "gateway_transaction_id": "gateway-tx-003",
            "status": "succeeded",
            "captured_amount": Decimal("150.00"),
        },
    )

    payment_service.gateway_factory.get_gateway.return_value = gateway

    result = await payment_service.capture_payment(
        transaction_id=transaction.id,
    )

    assert result.status == TransactionStatus.SUCCEEDED
    assert result.captured_amount == Decimal("150.00")

    gateway.capture_payment.assert_awaited_once_with(
        gateway_transaction_id="gateway-tx-003",
        amount=None,
    )


@pytest.mark.asyncio
async def test_capture_payment_rejects_non_authorized_transaction(
    payment_service,
):
    transaction = Mock()
    transaction.id = uuid4()
    transaction.status = TransactionStatus.PENDING

    payment_service.transaction_repository.get_by_id = AsyncMock(
        return_value=transaction,
    )

    with pytest.raises(InvalidTransactionStateError):
        await payment_service.capture_payment(
            transaction_id=transaction.id,
        )


@pytest.mark.asyncio
async def test_capture_payment_requires_gateway_transaction_id(
    payment_service,
):
    transaction = Mock()
    transaction.id = uuid4()
    transaction.status = TransactionStatus.AUTHORIZED
    transaction.gateway_transaction_id = None

    payment_service.transaction_repository.get_by_id = AsyncMock(
        return_value=transaction,
    )

    with pytest.raises(PaymentServiceError):
        await payment_service.capture_payment(
            transaction_id=transaction.id,
        )


@pytest.mark.asyncio
async def test_capture_payment_handles_gateway_failure(
    payment_service,
):
    transaction = Mock()
    transaction.id = uuid4()
    transaction.status = TransactionStatus.AUTHORIZED
    transaction.gateway_transaction_id = "gateway-tx-004"
    transaction.provider = PaymentProvider.STRIPE

    payment_service.transaction_repository.get_by_id = AsyncMock(
        return_value=transaction,
    )
    payment_service.transaction_repository.update = AsyncMock(
        return_value=transaction,
    )

    gateway = Mock()
    gateway.capture_payment = AsyncMock(
        side_effect=PaymentGatewayError(
            "Falha na captura."
        ),
    )

    payment_service.gateway_factory.get_gateway.return_value = gateway

    with pytest.raises(PaymentServiceError):
        await payment_service.capture_payment(
            transaction_id=transaction.id,
        )


@pytest.mark.asyncio
async def test_cancel_payment_without_gateway_transaction(
    payment_service,
):
    transaction = Mock()
    transaction.id = uuid4()
    transaction.status = TransactionStatus.PENDING
    transaction.gateway_transaction_id = None

    payment_service.transaction_repository.get_by_id = AsyncMock(
        return_value=transaction,
    )
    payment_service.transaction_repository.update = AsyncMock(
        return_value=transaction,
    )

    result = await payment_service.cancel_payment(
        transaction.id,
    )

    assert result.status == TransactionStatus.CANCELLED


@pytest.mark.asyncio
async def test_cancel_payment_with_gateway(
    payment_service,
):
    transaction = Mock()
    transaction.id = uuid4()
    transaction.status = TransactionStatus.AUTHORIZED
    transaction.gateway_transaction_id = "gateway-tx-005"
    transaction.provider = PaymentProvider.STRIPE

    payment_service.transaction_repository.get_by_id = AsyncMock(
        return_value=transaction,
    )
    payment_service.transaction_repository.update = AsyncMock(
        return_value=transaction,
    )

    gateway = Mock()
    gateway.cancel_payment = AsyncMock(
        return_value={
            "status": "cancelled",
        },
    )

    payment_service.gateway_factory.get_gateway.return_value = gateway

    result = await payment_service.cancel_payment(
        transaction.id,
    )

    assert result.status == TransactionStatus.CANCELLED

    gateway.cancel_payment.assert_awaited_once_with(
        gateway_transaction_id="gateway-tx-005",
    )


@pytest.mark.asyncio
async def test_cancel_payment_rejects_succeeded_transaction(
    payment_service,
):
    transaction = Mock()
    transaction.id = uuid4()
    transaction.status = TransactionStatus.SUCCEEDED

    payment_service.transaction_repository.get_by_id = AsyncMock(
        return_value=transaction,
    )

    with pytest.raises(InvalidTransactionStateError):
        await payment_service.cancel_payment(
            transaction.id,
        )


@pytest.mark.asyncio
async def test_cancel_payment_handles_gateway_error(
    payment_service,
):
    transaction = Mock()
    transaction.id = uuid4()
    transaction.status = TransactionStatus.AUTHORIZED
    transaction.gateway_transaction_id = "gateway-tx-006"
    transaction.provider = PaymentProvider.STRIPE

    payment_service.transaction_repository.get_by_id = AsyncMock(
        return_value=transaction,
    )

    gateway = Mock()
    gateway.cancel_payment = AsyncMock(
        side_effect=PaymentGatewayError(
            "Falha no cancelamento."
        ),
    )

    payment_service.gateway_factory.get_gateway.return_value = gateway

    with pytest.raises(PaymentServiceError):
        await payment_service.cancel_payment(
            transaction.id,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("gateway_status", "requires_capture", "expected_status"),
    [
        (
            "succeeded",
            False,
            TransactionStatus.SUCCEEDED,
        ),
        (
            "paid",
            False,
            TransactionStatus.SUCCEEDED,
        ),
        (
            "captured",
            False,
            TransactionStatus.SUCCEEDED,
        ),
        (
            "completed",
            False,
            TransactionStatus.SUCCEEDED,
        ),
        (
            "requires_capture",
            True,
            TransactionStatus.AUTHORIZED,
        ),
        (
            "processing",
            False,
            TransactionStatus.PROCESSING,
        ),
        (
            "declined",
            False,
            TransactionStatus.FAILED,
        ),
    ],
)
async def test_resolve_payment_status(
    gateway_status,
    requires_capture,
    expected_status,
):
    result = PaymentService._resolve_payment_status(
        {
            "status": gateway_status,
        },
        requires_capture,
    )

    assert result == expected_status