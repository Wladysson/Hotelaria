from decimal import Decimal
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from src.models.transactions import (
    PaymentProvider,
    TransactionStatus,
)
from src.schemas.payment import PaymentCreate
from src.services.payment_service import (
    InvalidTransactionStateError,
    PaymentServiceError,
)
from src.services.saga.payment_saga import (
    PaymentSaga,
    PaymentSagaCompensationError,
    PaymentSagaError,
)


@pytest.fixture
def payment_service():
    return Mock()


@pytest.fixture
def payment_saga(payment_service):
    return PaymentSaga(payment_service)


@pytest.fixture
def payment_data():
    return PaymentCreate(
        reservation_id=uuid4(),
        customer_id=uuid4(),
        amount=Decimal("150.00"),
        currency="BRL",
        payment_method_id=uuid4(),
        provider=PaymentProvider.STRIPE,
        description="Pagamento de reserva",
        requires_capture=True,
        idempotency_key=f"payment-{uuid4()}",
        metadata={
            "source": "saga-test",
        },
    )


def build_transaction(
    *,
    status: TransactionStatus,
):
    transaction = Mock()

    transaction.id = uuid4()
    transaction.reservation_id = uuid4()
    transaction.customer_id = uuid4()
    transaction.amount = Decimal("150.00")
    transaction.currency = "BRL"
    transaction.provider = PaymentProvider.STRIPE
    transaction.status = status
    transaction.gateway_transaction_id = "gateway-saga-001"
    transaction.captured_amount = Decimal("0.00")

    return transaction


@pytest.mark.asyncio
async def test_execute_returns_succeeded_transaction(
    payment_saga,
    payment_service,
    payment_data,
):
    transaction = build_transaction(
        status=TransactionStatus.SUCCEEDED,
    )

    payment_service.create_payment = AsyncMock(
        return_value=transaction,
    )

    result = await payment_saga.execute(
        payment_data,
    )

    assert result is transaction
    assert result.status == TransactionStatus.SUCCEEDED

    payment_service.create_payment.assert_awaited_once_with(
        payment_data,
    )


@pytest.mark.asyncio
async def test_execute_returns_authorized_transaction(
    payment_saga,
    payment_service,
    payment_data,
):
    transaction = build_transaction(
        status=TransactionStatus.AUTHORIZED,
    )

    payment_service.create_payment = AsyncMock(
        return_value=transaction,
    )

    result = await payment_saga.execute(
        payment_data,
    )

    assert result is transaction
    assert result.status == TransactionStatus.AUTHORIZED


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status",
    [
        TransactionStatus.FAILED,
        TransactionStatus.CANCELLED,
    ],
)
async def test_execute_rejects_failed_or_cancelled_transaction(
    payment_saga,
    payment_service,
    payment_data,
    status,
):
    transaction = build_transaction(
        status=status,
    )

    payment_service.create_payment = AsyncMock(
        return_value=transaction,
    )

    with pytest.raises(PaymentSagaError):
        await payment_saga.execute(
            payment_data,
        )


@pytest.mark.asyncio
async def test_execute_wraps_payment_service_error(
    payment_saga,
    payment_service,
    payment_data,
):
    payment_service.create_payment = AsyncMock(
        side_effect=PaymentServiceError(
            "Falha no pagamento."
        ),
    )

    with pytest.raises(PaymentSagaError) as exc_info:
        await payment_saga.execute(
            payment_data,
        )

    assert "criação" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_capture_success(
    payment_saga,
    payment_service,
):
    transaction = build_transaction(
        status=TransactionStatus.AUTHORIZED,
    )

    payment_service.get_payment = AsyncMock(
        return_value=transaction,
    )

    captured_transaction = build_transaction(
        status=TransactionStatus.SUCCEEDED,
    )

    payment_service.capture_payment = AsyncMock(
        return_value=captured_transaction,
    )

    result = await payment_saga.capture(
        transaction_id=transaction.id,
    )

    assert result is captured_transaction
    assert result.status == TransactionStatus.SUCCEEDED

    payment_service.get_payment.assert_awaited_once_with(
        transaction.id,
    )

    payment_service.capture_payment.assert_awaited_once_with(
        transaction_id=transaction.id,
        amount=None,
    )


@pytest.mark.asyncio
async def test_capture_rejects_non_authorized_transaction(
    payment_saga,
    payment_service,
):
    transaction = build_transaction(
        status=TransactionStatus.PENDING,
    )

    payment_service.get_payment = AsyncMock(
        return_value=transaction,
    )

    with pytest.raises(InvalidTransactionStateError):
        await payment_saga.capture(
            transaction_id=transaction.id,
        )

    payment_service.capture_payment = AsyncMock()

    payment_service.capture_payment.assert_not_awaited()


@pytest.mark.asyncio
async def test_capture_failure_triggers_compensation(
    payment_saga,
    payment_service,
):
    transaction = build_transaction(
        status=TransactionStatus.AUTHORIZED,
    )

    payment_service.get_payment = AsyncMock(
        side_effect=[
            transaction,
            transaction,
        ],
    )

    payment_service.capture_payment = AsyncMock(
        side_effect=PaymentServiceError(
            "Falha na captura."
        ),
    )

    payment_service.cancel_payment = AsyncMock(
        return_value=build_transaction(
            status=TransactionStatus.CANCELLED,
        ),
    )

    with pytest.raises(PaymentSagaError):
        await payment_saga.capture(
            transaction_id=transaction.id,
        )

    payment_service.cancel_payment.assert_awaited_once_with(
        transaction.id,
    )


@pytest.mark.asyncio
async def test_capture_failure_compensation_failure(
    payment_saga,
    payment_service,
):
    transaction = build_transaction(
        status=TransactionStatus.AUTHORIZED,
    )

    payment_service.get_payment = AsyncMock(
        side_effect=[
            transaction,
            transaction,
        ],
    )

    payment_service.capture_payment = AsyncMock(
        side_effect=PaymentServiceError(
            "Falha na captura."
        ),
    )

    payment_service.cancel_payment = AsyncMock(
        side_effect=PaymentServiceError(
            "Falha na compensação."
        ),
    )

    with pytest.raises(PaymentSagaCompensationError):
        await payment_saga.capture(
            transaction_id=transaction.id,
        )


@pytest.mark.asyncio
async def test_capture_failure_does_not_compensate_if_state_changed(
    payment_saga,
    payment_service,
):
    authorized_transaction = build_transaction(
        status=TransactionStatus.AUTHORIZED,
    )

    succeeded_transaction = build_transaction(
        status=TransactionStatus.SUCCEEDED,
    )

    payment_service.get_payment = AsyncMock(
        side_effect=[
            authorized_transaction,
            succeeded_transaction,
        ],
    )

    payment_service.capture_payment = AsyncMock(
        side_effect=PaymentServiceError(
            "Falha após processamento externo."
        ),
    )

    payment_service.cancel_payment = AsyncMock()

    with pytest.raises(PaymentSagaError):
        await payment_saga.capture(
            transaction_id=authorized_transaction.id,
        )

    payment_service.cancel_payment.assert_not_awaited()


@pytest.mark.asyncio
async def test_cancel_success(
    payment_saga,
    payment_service,
):
    transaction_id = uuid4()

    cancelled_transaction = build_transaction(
        status=TransactionStatus.CANCELLED,
    )

    payment_service.cancel_payment = AsyncMock(
        return_value=cancelled_transaction,
    )

    result = await payment_saga.cancel(
        transaction_id,
    )

    assert result is cancelled_transaction
    assert result.status == TransactionStatus.CANCELLED

    payment_service.cancel_payment.assert_awaited_once_with(
        transaction_id,
    )


@pytest.mark.asyncio
async def test_cancel_wraps_service_error(
    payment_saga,
    payment_service,
):
    transaction_id = uuid4()

    payment_service.cancel_payment = AsyncMock(
        side_effect=PaymentServiceError(
            "Falha no cancelamento."
        ),
    )

    with pytest.raises(PaymentSagaError):
        await payment_saga.cancel(
            transaction_id,
        )


@pytest.mark.asyncio
async def test_execute_with_capture_success(
    payment_saga,
    payment_service,
    payment_data,
):
    authorized_transaction = build_transaction(
        status=TransactionStatus.AUTHORIZED,
    )

    captured_transaction = build_transaction(
        status=TransactionStatus.SUCCEEDED,
    )

    payment_service.create_payment = AsyncMock(
        return_value=authorized_transaction,
    )

    payment_service.capture_payment = AsyncMock(
        return_value=captured_transaction,
    )

    result = await payment_saga.execute_with_capture(
        payment_data,
    )

    assert result is captured_transaction
    assert result.status == TransactionStatus.SUCCEEDED

    payment_service.create_payment.assert_awaited_once_with(
        payment_data,
    )

    payment_service.capture_payment.assert_awaited_once_with(
        transaction_id=authorized_transaction.id,
    )


@pytest.mark.asyncio
async def test_execute_with_capture_returns_already_succeeded_payment(
    payment_saga,
    payment_service,
    payment_data,
):
    transaction = build_transaction(
        status=TransactionStatus.SUCCEEDED,
    )

    payment_service.create_payment = AsyncMock(
        return_value=transaction,
    )

    payment_service.capture_payment = AsyncMock()

    result = await payment_saga.execute_with_capture(
        payment_data,
    )

    assert result is transaction

    payment_service.capture_payment.assert_not_awaited()


@pytest.mark.asyncio
async def test_execute_with_capture_rejects_failed_payment(
    payment_saga,
    payment_service,
    payment_data,
):
    transaction = build_transaction(
        status=TransactionStatus.FAILED,
    )

    payment_service.create_payment = AsyncMock(
        return_value=transaction,
    )

    with pytest.raises(PaymentSagaError):
        await payment_saga.execute_with_capture(
            payment_data,
        )


@pytest.mark.asyncio
async def test_execute_with_capture_compensates_capture_failure(
    payment_saga,
    payment_service,
    payment_data,
):
    transaction = build_transaction(
        status=TransactionStatus.AUTHORIZED,
    )

    payment_service.create_payment = AsyncMock(
        return_value=transaction,
    )

    payment_service.capture_payment = AsyncMock(
        side_effect=PaymentServiceError(
            "Falha na captura."
        ),
    )

    payment_service.get_payment = AsyncMock(
        return_value=transaction,
    )

    payment_service.cancel_payment = AsyncMock(
        return_value=build_transaction(
            status=TransactionStatus.CANCELLED,
        ),
    )

    with pytest.raises(PaymentSagaError):
        await payment_saga.execute_with_capture(
            payment_data,
        )

    payment_service.cancel_payment.assert_awaited_once_with(
        transaction.id,
    )


@pytest.mark.asyncio
async def test_execute_with_capture_raises_when_compensation_fails(
    payment_saga,
    payment_service,
    payment_data,
):
    transaction = build_transaction(
        status=TransactionStatus.AUTHORIZED,
    )

    payment_service.create_payment = AsyncMock(
        return_value=transaction,
    )

    payment_service.capture_payment = AsyncMock(
        side_effect=PaymentServiceError(
            "Falha na captura."
        ),
    )

    payment_service.get_payment = AsyncMock(
        return_value=transaction,
    )

    payment_service.cancel_payment = AsyncMock(
        side_effect=PaymentServiceError(
            "Falha na compensação."
        ),
    )

    with pytest.raises(PaymentSagaCompensationError):
        await payment_saga.execute_with_capture(
            payment_data,
        )


@pytest.mark.asyncio
async def test_execute_with_capture_does_not_compensate_after_state_change(
    payment_saga,
    payment_service,
    payment_data,
):
    transaction = build_transaction(
        status=TransactionStatus.AUTHORIZED,
    )

    succeeded_transaction = build_transaction(
        status=TransactionStatus.SUCCEEDED,
    )

    payment_service.create_payment = AsyncMock(
        return_value=transaction,
    )

    payment_service.capture_payment = AsyncMock(
        side_effect=PaymentServiceError(
            "Falha durante captura."
        ),
    )

    payment_service.get_payment = AsyncMock(
        return_value=succeeded_transaction,
    )

    payment_service.cancel_payment = AsyncMock()

    with pytest.raises(PaymentSagaError):
        await payment_saga.execute_with_capture(
            payment_data,
        )

    payment_service.cancel_payment.assert_not_awaited()


@pytest.mark.asyncio
async def test_compensation_only_cancels_authorized_transaction(
    payment_saga,
    payment_service,
):
    transaction_id = uuid4()

    transaction = build_transaction(
        status=TransactionStatus.AUTHORIZED,
    )

    payment_service.get_payment = AsyncMock(
        return_value=transaction,
    )

    payment_service.cancel_payment = AsyncMock(
        return_value=build_transaction(
            status=TransactionStatus.CANCELLED,
        ),
    )

    await payment_saga._compensate_capture_failure(
        transaction_id,
    )

    payment_service.cancel_payment.assert_awaited_once_with(
        transaction_id,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status",
    [
        TransactionStatus.SUCCEEDED,
        TransactionStatus.CANCELLED,
        TransactionStatus.FAILED,
        TransactionStatus.PROCESSING,
    ],
)
async def test_compensation_ignores_non_authorized_transaction(
    payment_saga,
    payment_service,
    status,
):
    transaction_id = uuid4()

    transaction = build_transaction(
        status=status,
    )

    payment_service.get_payment = AsyncMock(
        return_value=transaction,
    )

    payment_service.cancel_payment = AsyncMock()

    await payment_saga._compensate_capture_failure(
        transaction_id,
    )

    payment_service.cancel_payment.assert_not_awaited()