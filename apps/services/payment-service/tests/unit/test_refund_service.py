from decimal import Decimal
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from src.core.payment_gateway import PaymentGatewayError
from src.models.refund import (
    RefundReason,
    RefundStatus,
)
from src.models.transactions import (
    PaymentProvider,
    TransactionStatus,
)
from src.schemas.refund import RefundCreate
from src.services.refund_service import (
    RefundAlreadyProcessedError,
    RefundAmountExceededError,
    RefundNotAllowedError,
    RefundNotFoundError,
    RefundService,
    RefundServiceError,
)


@pytest.fixture
def refund_service(db_session):
    gateway_factory = Mock()

    return RefundService(
        session=db_session,
        gateway_factory=gateway_factory,
    )


@pytest.fixture
def refund_data(
    fake_transaction_id,
    fake_reservation_id,
):
    return RefundCreate(
        transaction_id=fake_transaction_id,
        reservation_id=fake_reservation_id,
        amount=Decimal("50.00"),
        reason=RefundReason.CUSTOMER_REQUEST,
        idempotency_key=f"refund-{uuid4()}",
        description="Reembolso de teste",
    )


@pytest.fixture
def refundable_transaction():
    transaction = Mock()

    transaction.id = uuid4()
    transaction.reservation_id = uuid4()
    transaction.amount = Decimal("150.00")
    transaction.currency = "BRL"
    transaction.status = TransactionStatus.SUCCEEDED
    transaction.captured_amount = Decimal("150.00")
    transaction.refunded_amount = Decimal("0.00")
    transaction.gateway_transaction_id = "gateway-tx-refund-001"
    transaction.provider = PaymentProvider.STRIPE

    return transaction


@pytest.mark.asyncio
async def test_create_refund_success(
    refund_service,
    refund_data,
    refundable_transaction,
):
    refund_service._get_by_idempotency_key = AsyncMock(
        return_value=None,
    )

    refund_service.transaction_repository.get_by_id = AsyncMock(
        return_value=refundable_transaction,
    )

    gateway = Mock()
    gateway.refund_payment = AsyncMock(
        return_value={
            "id": "gateway-refund-001",
            "gateway_refund_id": "gateway-refund-001",
            "status": "succeeded",
        },
    )

    refund_service.gateway_factory.get_gateway.return_value = gateway

    refund = await refund_service.create_refund(
        refund_data,
    )

    assert refund.id is not None
    assert refund.transaction_id == refundable_transaction.id
    assert refund.amount == Decimal("50.00")
    assert refund.currency == "BRL"
    assert refund.status == RefundStatus.SUCCEEDED
    assert refund.gateway_refund_id == "gateway-refund-001"

    assert refundable_transaction.refunded_amount == Decimal("50.00")
    assert refundable_transaction.status == TransactionStatus.PARTIALLY_REFUNDED

    gateway.refund_payment.assert_awaited_once_with(
        gateway_transaction_id="gateway-tx-refund-001",
        amount=Decimal("50.00"),
        reason="customer_request",
    )


@pytest.mark.asyncio
async def test_create_full_refund_changes_transaction_status(
    refund_service,
    refund_data,
    refundable_transaction,
):
    refund_data.amount = Decimal("150.00")

    refund_service._get_by_idempotency_key = AsyncMock(
        return_value=None,
    )

    refund_service.transaction_repository.get_by_id = AsyncMock(
        return_value=refundable_transaction,
    )

    gateway = Mock()
    gateway.refund_payment = AsyncMock(
        return_value={
            "id": "gateway-refund-full",
            "gateway_refund_id": "gateway-refund-full",
            "status": "succeeded",
        },
    )

    refund_service.gateway_factory.get_gateway.return_value = gateway

    refund = await refund_service.create_refund(
        refund_data,
    )

    assert refund.status == RefundStatus.SUCCEEDED
    assert refundable_transaction.refunded_amount == Decimal("150.00")
    assert refundable_transaction.status == TransactionStatus.REFUNDED


@pytest.mark.asyncio
async def test_create_refund_rejects_duplicate_idempotency(
    refund_service,
    refund_data,
):
    existing_refund = Mock()

    refund_service._get_by_idempotency_key = AsyncMock(
        return_value=existing_refund,
    )

    with pytest.raises(RefundAlreadyProcessedError):
        await refund_service.create_refund(
            refund_data,
        )


@pytest.mark.asyncio
async def test_create_refund_requires_existing_transaction(
    refund_service,
    refund_data,
):
    refund_service._get_by_idempotency_key = AsyncMock(
        return_value=None,
    )

    refund_service.transaction_repository.get_by_id = AsyncMock(
        return_value=None,
    )

    with pytest.raises(RefundServiceError) as exc_info:
        await refund_service.create_refund(
            refund_data,
        )

    assert "original" in str(exc_info.value).lower()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "transaction_status",
    [
        TransactionStatus.PENDING,
        TransactionStatus.AUTHORIZED,
        TransactionStatus.PROCESSING,
        TransactionStatus.FAILED,
        TransactionStatus.CANCELLED,
    ],
)
async def test_create_refund_rejects_non_refundable_transaction(
    refund_service,
    refund_data,
    transaction_status,
):
    transaction = Mock()

    transaction.id = uuid4()
    transaction.status = transaction_status
    transaction.captured_amount = Decimal("150.00")
    transaction.refunded_amount = Decimal("0.00")

    refund_service._get_by_idempotency_key = AsyncMock(
        return_value=None,
    )

    refund_service.transaction_repository.get_by_id = AsyncMock(
        return_value=transaction,
    )

    with pytest.raises(RefundNotAllowedError):
        await refund_service.create_refund(
            refund_data,
        )


@pytest.mark.asyncio
async def test_create_refund_rejects_excessive_amount(
    refund_service,
    refund_data,
    refundable_transaction,
):
    refund_data.amount = Decimal("151.00")

    refund_service._get_by_idempotency_key = AsyncMock(
        return_value=None,
    )

    refund_service.transaction_repository.get_by_id = AsyncMock(
        return_value=refundable_transaction,
    )

    with pytest.raises(RefundAmountExceededError):
        await refund_service.create_refund(
            refund_data,
        )


@pytest.mark.asyncio
async def test_create_refund_considers_previous_refunds(
    refund_service,
    refund_data,
    refundable_transaction,
):
    refundable_transaction.refunded_amount = Decimal("120.00")
    refund_data.amount = Decimal("31.00")

    refund_service._get_by_idempotency_key = AsyncMock(
        return_value=None,
    )

    refund_service.transaction_repository.get_by_id = AsyncMock(
        return_value=refundable_transaction,
    )

    with pytest.raises(RefundAmountExceededError):
        await refund_service.create_refund(
            refund_data,
        )


@pytest.mark.asyncio
async def test_create_refund_requires_gateway_transaction_id(
    refund_service,
    refund_data,
    refundable_transaction,
):
    refundable_transaction.gateway_transaction_id = None

    refund_service._get_by_idempotency_key = AsyncMock(
        return_value=None,
    )

    refund_service.transaction_repository.get_by_id = AsyncMock(
        return_value=refundable_transaction,
    )

    with pytest.raises(RefundServiceError) as exc_info:
        await refund_service.create_refund(
            refund_data,
        )

    assert "identificador" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_create_refund_handles_gateway_failure(
    refund_service,
    refund_data,
    refundable_transaction,
):
    refund_service._get_by_idempotency_key = AsyncMock(
        return_value=None,
    )

    refund_service.transaction_repository.get_by_id = AsyncMock(
        return_value=refundable_transaction,
    )

    gateway = Mock()
    gateway.refund_payment = AsyncMock(
        side_effect=PaymentGatewayError(
            "Gateway indisponível."
        ),
    )

    refund_service.gateway_factory.get_gateway.return_value = gateway

    with pytest.raises(RefundServiceError) as exc_info:
        await refund_service.create_refund(
            refund_data,
        )

    assert "gateway" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_get_refund_success(
    refund_service,
):
    refund = Mock()
    refund.id = uuid4()

    refund_service.session.execute = AsyncMock()

    result_mock = Mock()
    result_mock.scalar_one_or_none.return_value = refund

    refund_service.session.execute.return_value = result_mock

    result = await refund_service.get_refund(
        refund.id,
    )

    assert result is refund


@pytest.mark.asyncio
async def test_get_refund_not_found(
    refund_service,
):
    refund_id = uuid4()

    refund_service.session.execute = AsyncMock()

    result_mock = Mock()
    result_mock.scalar_one_or_none.return_value = None

    refund_service.session.execute.return_value = result_mock

    with pytest.raises(RefundNotFoundError):
        await refund_service.get_refund(
            refund_id,
        )


@pytest.mark.asyncio
async def test_get_refund_by_idempotency_key(
    refund_service,
):
    refund = Mock()

    refund_service.session.execute = AsyncMock()

    result_mock = Mock()
    result_mock.scalar_one_or_none.return_value = refund

    refund_service.session.execute.return_value = result_mock

    result = await refund_service.get_refund_by_idempotency_key(
        "refund-key-001",
    )

    assert result is refund


@pytest.mark.asyncio
async def test_get_refund_by_idempotency_key_returns_none(
    refund_service,
):
    refund_service.session.execute = AsyncMock()

    result_mock = Mock()
    result_mock.scalar_one_or_none.return_value = None

    refund_service.session.execute.return_value = result_mock

    result = await refund_service.get_refund_by_idempotency_key(
        "refund-key-002",
    )

    assert result is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("gateway_status", "expected_status"),
    [
        ("succeeded", RefundStatus.SUCCEEDED),
        ("refunded", RefundStatus.SUCCEEDED),
        ("completed", RefundStatus.SUCCEEDED),
        ("processed", RefundStatus.SUCCEEDED),
        ("failed", RefundStatus.FAILED),
        ("declined", RefundStatus.FAILED),
        ("rejected", RefundStatus.FAILED),
        ("pending", RefundStatus.PROCESSING),
    ],
)
async def test_resolve_refund_status(
    gateway_status,
    expected_status,
):
    result = RefundService._resolve_refund_status(
        {
            "status": gateway_status,
        },
    )

    assert result == expected_status