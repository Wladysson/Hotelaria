from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from src.models.transactions import (
    PaymentProvider,
    TransactionStatus,
)
from src.workers.tasks.payment_tasks import (
    capture_authorized_payment,
    cancel_pending_payment,
    process_payment,
)


def build_transaction(
    *,
    status: TransactionStatus,
):
    transaction = Mock()

    transaction.id = uuid4()
    transaction.provider = PaymentProvider.STRIPE
    transaction.status = status
    transaction.gateway_transaction_id = "gateway-tx-001"
    transaction.captured_amount = Decimal("0.00")
    transaction.amount = Decimal("150.00")

    return transaction


@pytest.mark.asyncio
async def test_process_payment_returns_failed_when_transaction_not_found():
    transaction_repository = Mock()
    transaction_repository.get_by_id = AsyncMock(
        return_value=None,
    )

    session = AsyncMock()

    session_context = Mock()
    session_context.__aenter__ = AsyncMock(
        return_value=session,
    )
    session_context.__aexit__ = AsyncMock(
        return_value=None,
    )

    with patch(
        "src.workers.tasks.payment_tasks.AsyncSessionLocal",
        return_value=session_context,
    ):
        with patch(
            "src.workers.tasks.payment_tasks.TransactionRepository",
            return_value=transaction_repository,
        ):
            result = await process_payment(
                uuid4(),
            )

    assert result.processed is False
    assert result.status == TransactionStatus.FAILED
    assert result.error == "Transação não encontrada."


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status",
    [
        TransactionStatus.SUCCEEDED,
        TransactionStatus.CANCELLED,
        TransactionStatus.REFUNDED,
    ],
)
async def test_process_payment_ignores_finalized_transaction(
    status,
):
    transaction = build_transaction(
        status=status,
    )

    transaction_repository = Mock()
    transaction_repository.get_by_id = AsyncMock(
        return_value=transaction,
    )

    session = AsyncMock()

    session_context = Mock()
    session_context.__aenter__ = AsyncMock(
        return_value=session,
    )
    session_context.__aexit__ = AsyncMock(
        return_value=None,
    )

    with patch(
        "src.workers.tasks.payment_tasks.AsyncSessionLocal",
        return_value=session_context,
    ):
        with patch(
            "src.workers.tasks.payment_tasks.TransactionRepository",
            return_value=transaction_repository,
        ):
            result = await process_payment(
                transaction.id,
            )

    assert result.processed is False
    assert result.status == status


@pytest.mark.asyncio
async def test_process_payment_marks_transaction_as_succeeded():
    transaction = build_transaction(
        status=TransactionStatus.PROCESSING,
    )

    transaction_repository = Mock()
    transaction_repository.get_by_id = AsyncMock(
        return_value=transaction,
    )

    gateway = Mock()
    gateway.get_payment = AsyncMock(
        return_value={
            "status": "succeeded",
            "captured_amount": Decimal("150.00"),
        },
    )

    gateway_factory = Mock()
    gateway_factory.get_gateway.return_value = gateway

    session = AsyncMock()

    session_context = Mock()
    session_context.__aenter__ = AsyncMock(
        return_value=session,
    )
    session_context.__aexit__ = AsyncMock(
        return_value=None,
    )

    with patch(
        "src.workers.tasks.payment_tasks.AsyncSessionLocal",
        return_value=session_context,
    ):
        with patch(
            "src.workers.tasks.payment_tasks.TransactionRepository",
            return_value=transaction_repository,
        ):
            with patch(
                "src.workers.tasks.payment_tasks.GatewayFactory",
                return_value=gateway_factory,
            ):
                result = await process_payment(
                    transaction.id,
                )

    assert result.processed is True
    assert result.status == TransactionStatus.SUCCEEDED
    assert transaction.status == TransactionStatus.SUCCEEDED
    assert transaction.captured_amount == Decimal("150.00")

    gateway.get_payment.assert_awaited_once_with(
        gateway_transaction_id="gateway-tx-001",
    )

    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_payment_marks_transaction_as_failed():
    transaction = build_transaction(
        status=TransactionStatus.PROCESSING,
    )

    transaction_repository = Mock()
    transaction_repository.get_by_id = AsyncMock(
        return_value=transaction,
    )

    gateway = Mock()
    gateway.get_payment = AsyncMock(
        return_value={
            "status": "failed",
        },
    )

    gateway_factory = Mock()
    gateway_factory.get_gateway.return_value = gateway

    session = AsyncMock()

    session_context = Mock()
    session_context.__aenter__ = AsyncMock(
        return_value=session,
    )
    session_context.__aexit__ = AsyncMock(
        return_value=None,
    )

    with patch(
        "src.workers.tasks.payment_tasks.AsyncSessionLocal",
        return_value=session_context,
    ):
        with patch(
            "src.workers.tasks.payment_tasks.TransactionRepository",
            return_value=transaction_repository,
        ):
            with patch(
                "src.workers.tasks.payment_tasks.GatewayFactory",
                return_value=gateway_factory,
            ):
                result = await process_payment(
                    transaction.id,
                )

    assert result.processed is True
    assert result.status == TransactionStatus.FAILED
    assert transaction.failure_code == "gateway_failed"

    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_payment_marks_transaction_as_cancelled():
    transaction = build_transaction(
        status=TransactionStatus.PROCESSING,
    )

    transaction_repository = Mock()
    transaction_repository.get_by_id = AsyncMock(
        return_value=transaction,
    )

    gateway = Mock()
    gateway.get_payment = AsyncMock(
        return_value={
            "status": "cancelled",
        },
    )

    gateway_factory = Mock()
    gateway_factory.get_gateway.return_value = gateway

    session = AsyncMock()

    session_context = Mock()
    session_context.__aenter__ = AsyncMock(
        return_value=session,
    )
    session_context.__aexit__ = AsyncMock(
        return_value=None,
    )

    with patch(
        "src.workers.tasks.payment_tasks.AsyncSessionLocal",
        return_value=session_context,
    ):
        with patch(
            "src.workers.tasks.payment_tasks.TransactionRepository",
            return_value=transaction_repository,
        ):
            with patch(
                "src.workers.tasks.payment_tasks.GatewayFactory",
                return_value=gateway_factory,
            ):
                result = await process_payment(
                    transaction.id,
                )

    assert result.status == TransactionStatus.CANCELLED
    assert transaction.status == TransactionStatus.CANCELLED


@pytest.mark.asyncio
async def test_process_payment_keeps_processing_for_unknown_status():
    transaction = build_transaction(
        status=TransactionStatus.PROCESSING,
    )

    transaction_repository = Mock()
    transaction_repository.get_by_id = AsyncMock(
        return_value=transaction,
    )

    gateway = Mock()
    gateway.get_payment = AsyncMock(
        return_value={
            "status": "requires_action",
        },
    )

    gateway_factory = Mock()
    gateway_factory.get_gateway.return_value = gateway

    session = AsyncMock()

    session_context = Mock()
    session_context.__aenter__ = AsyncMock(
        return_value=session,
    )
    session_context.__aexit__ = AsyncMock(
        return_value=None,
    )

    with patch(
        "src.workers.tasks.payment_tasks.AsyncSessionLocal",
        return_value=session_context,
    ):
        with patch(
            "src.workers.tasks.payment_tasks.TransactionRepository",
            return_value=transaction_repository,
        ):
            with patch(
                "src.workers.tasks.payment_tasks.GatewayFactory",
                return_value=gateway_factory,
            ):
                result = await process_payment(
                    transaction.id,
                )

    assert result.status == TransactionStatus.PROCESSING
    assert result.processed is True


@pytest.mark.asyncio
async def test_process_payment_rolls_back_on_unexpected_error():
    transaction = build_transaction(
        status=TransactionStatus.PROCESSING,
    )

    transaction_repository = Mock()
    transaction_repository.get_by_id = AsyncMock(
        return_value=transaction,
    )

    gateway_factory = Mock()
    gateway_factory.get_gateway.side_effect = RuntimeError(
        "Unexpected error"
    )

    session = AsyncMock()

    session_context = Mock()
    session_context.__aenter__ = AsyncMock(
        return_value=session,
    )
    session_context.__aexit__ = AsyncMock(
        return_value=None,
    )

    with patch(
        "src.workers.tasks.payment_tasks.AsyncSessionLocal",
        return_value=session_context,
    ):
        with patch(
            "src.workers.tasks.payment_tasks.TransactionRepository",
            return_value=transaction_repository,
        ):
            with patch(
                "src.workers.tasks.payment_tasks.GatewayFactory",
                return_value=gateway_factory,
            ):
                result = await process_payment(
                    transaction.id,
                )

    assert result.processed is False
    assert result.status == TransactionStatus.FAILED

    session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_capture_authorized_payment_returns_not_found():
    transaction_repository = Mock()
    transaction_repository.get_by_id = AsyncMock(
        return_value=None,
    )

    session = AsyncMock()

    session_context = Mock()
    session_context.__aenter__ = AsyncMock(
        return_value=session,
    )
    session_context.__aexit__ = AsyncMock(
        return_value=None,
    )

    with patch(
        "src.workers.tasks.payment_tasks.AsyncSessionLocal",
        return_value=session_context,
    ):
        with patch(
            "src.workers.tasks.payment_tasks.TransactionRepository",
            return_value=transaction_repository,
        ):
            result = await capture_authorized_payment(
                uuid4(),
            )

    assert result.processed is False
    assert result.status == TransactionStatus.FAILED
    assert result.error == "Transação não encontrada."


@pytest.mark.asyncio
async def test_capture_authorized_payment_rejects_non_authorized_transaction():
    transaction = build_transaction(
        status=TransactionStatus.PENDING,
    )

    transaction_repository = Mock()
    transaction_repository.get_by_id = AsyncMock(
        return_value=transaction,
    )

    session = AsyncMock()

    session_context = Mock()
    session_context.__aenter__ = AsyncMock(
        return_value=session,
    )
    session_context.__aexit__ = AsyncMock(
        return_value=None,
    )

    with patch(
        "src.workers.tasks.payment_tasks.AsyncSessionLocal",
        return_value=session_context,
    ):
        with patch(
            "src.workers.tasks.payment_tasks.TransactionRepository",
            return_value=transaction_repository,
        ):
            result = await capture_authorized_payment(
                transaction.id,
            )

    assert result.processed is False
    assert result.status == TransactionStatus.PENDING
    assert "autorizada" in result.error


@pytest.mark.asyncio
async def test_capture_authorized_payment_success():
    transaction = build_transaction(
        status=TransactionStatus.AUTHORIZED,
    )

    transaction_repository = Mock()
    transaction_repository.get_by_id = AsyncMock(
        return_value=transaction,
    )

    captured_transaction = build_transaction(
        status=TransactionStatus.SUCCEEDED,
    )

    payment_service = Mock()
    payment_service.capture_payment = AsyncMock(
        return_value=captured_transaction,
    )

    saga = Mock()
    saga.capture = AsyncMock(
        return_value=captured_transaction,
    )

    session = AsyncMock()

    session_context = Mock()
    session_context.__aenter__ = AsyncMock(
        return_value=session,
    )
    session_context.__aexit__ = AsyncMock(
        return_value=None,
    )

    with patch(
        "src.workers.tasks.payment_tasks.AsyncSessionLocal",
        return_value=session_context,
    ):
        with patch(
            "src.workers.tasks.payment_tasks.TransactionRepository",
            return_value=transaction_repository,
        ):
            with patch(
                "src.workers.tasks.payment_tasks.PaymentService",
                return_value=payment_service,
            ):
                with patch(
                    "src.workers.tasks.payment_tasks.PaymentSaga",
                    return_value=saga,
                ):
                    result = await capture_authorized_payment(
                        transaction.id,
                        amount=Decimal("150.00"),
                    )

    assert result.processed is True
    assert result.status == TransactionStatus.SUCCEEDED

    saga.capture.assert_awaited_once_with(
        transaction_id=transaction.id,
        amount=Decimal("150.00"),
    )


@pytest.mark.asyncio
async def test_capture_authorized_payment_handles_failure():
    transaction = build_transaction(
        status=TransactionStatus.AUTHORIZED,
    )

    transaction_repository = Mock()
    transaction_repository.get_by_id = AsyncMock(
        return_value=transaction,
    )

    saga = Mock()
    saga.capture = AsyncMock(
        side_effect=RuntimeError(
            "Capture failed"
        ),
    )

    session = AsyncMock()

    session_context = Mock()
    session_context.__aenter__ = AsyncMock(
        return_value=session,
    )
    session_context.__aexit__ = AsyncMock(
        return_value=None,
    )

    with patch(
        "src.workers.tasks.payment_tasks.AsyncSessionLocal",
        return_value=session_context,
    ):
        with patch(
            "src.workers.tasks.payment_tasks.TransactionRepository",
            return_value=transaction_repository,
        ):
            with patch(
                "src.workers.tasks.payment_tasks.PaymentService",
            ):
                with patch(
                    "src.workers.tasks.payment_tasks.PaymentSaga",
                    return_value=saga,
                ):
                    result = await capture_authorized_payment(
                        transaction.id,
                    )

    assert result.processed is False
    assert result.status == TransactionStatus.FAILED
    assert result.error == "Capture failed"

    session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_cancel_pending_payment_returns_not_found():
    transaction_repository = Mock()
    transaction_repository.get_by_id = AsyncMock(
        return_value=None,
    )

    session = AsyncMock()

    session_context = Mock()
    session_context.__aenter__ = AsyncMock(
        return_value=session,
    )
    session_context.__aexit__ = AsyncMock(
        return_value=None,
    )

    with patch(
        "src.workers.tasks.payment_tasks.AsyncSessionLocal",
        return_value=session_context,
    ):
        with patch(
            "src.workers.tasks.payment_tasks.TransactionRepository",
            return_value=transaction_repository,
        ):
            result = await cancel_pending_payment(
                uuid4(),
            )

    assert result.processed is False
    assert result.status == TransactionStatus.FAILED


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status",
    [
        TransactionStatus.CANCELLED,
        TransactionStatus.SUCCEEDED,
        TransactionStatus.REFUNDED,
    ],
)
async def test_cancel_pending_payment_ignores_finalized_transaction(
    status,
):
    transaction = build_transaction(
        status=status,
    )

    transaction_repository = Mock()
    transaction_repository.get_by_id = AsyncMock(
        return_value=transaction,
    )

    session = AsyncMock()

    session_context = Mock()
    session_context.__aenter__ = AsyncMock(
        return_value=session,
    )
    session_context.__aexit__ = AsyncMock(
        return_value=None,
    )

    with patch(
        "src.workers.tasks.payment_tasks.AsyncSessionLocal",
        return_value=session_context,
    ):
        with patch(
            "src.workers.tasks.payment_tasks.TransactionRepository",
            return_value=transaction_repository,
        ):
            result = await cancel_pending_payment(
                transaction.id,
            )

    assert result.processed is False
    assert result.status == status


@pytest.mark.asyncio
async def test_cancel_pending_payment_success():
    transaction = build_transaction(
        status=TransactionStatus.PENDING,
    )

    transaction_repository = Mock()
    transaction_repository.get_by_id = AsyncMock(
        return_value=transaction,
    )

    cancelled_transaction = build_transaction(
        status=TransactionStatus.CANCELLED,
    )

    saga = Mock()
    saga.cancel = AsyncMock(
        return_value=cancelled_transaction,
    )

    session = AsyncMock()

    session_context = Mock()
    session_context.__aenter__ = AsyncMock(
        return_value=session,
    )
    session_context.__aexit__ = AsyncMock(
        return_value=None,
    )

    with patch(
        "src.workers.tasks.payment_tasks.AsyncSessionLocal",
        return_value=session_context,
    ):
        with patch(
            "src.workers.tasks.payment_tasks.TransactionRepository",
            return_value=transaction_repository,
        ):
            with patch(
                "src.workers.tasks.payment_tasks.PaymentService",
            ):
                with patch(
                    "src.workers.tasks.payment_tasks.PaymentSaga",
                    return_value=saga,
                ):
                    result = await cancel_pending_payment(
                        transaction.id,
                    )

    assert result.processed is True
    assert result.status == TransactionStatus.CANCELLED

    saga.cancel.assert_awaited_once_with(
        transaction_id=transaction.id,
    )


@pytest.mark.asyncio
async def test_cancel_pending_payment_handles_failure():
    transaction = build_transaction(
        status=TransactionStatus.PENDING,
    )

    transaction_repository = Mock()
    transaction_repository.get_by_id = AsyncMock(
        return_value=transaction,
    )

    saga = Mock()
    saga.cancel = AsyncMock(
        side_effect=RuntimeError(
            "Cancel failed"
        ),
    )

    session = AsyncMock()

    session_context = Mock()
    session_context.__aenter__ = AsyncMock(
        return_value=session,
    )
    session_context.__aexit__ = AsyncMock(
        return_value=None,
    )

    with patch(
        "src.workers.tasks.payment_tasks.AsyncSessionLocal",
        return_value=session_context,
    ):
        with patch(
            "src.workers.tasks.payment_tasks.TransactionRepository",
            return_value=transaction_repository,
        ):
            with patch(
                "src.workers.tasks.payment_tasks.PaymentService",
            ):
                with patch(
                    "src.workers.tasks.payment_tasks.PaymentSaga",
                    return_value=saga,
                ):
                    result = await cancel_pending_payment(
                        transaction.id,
                    )

    assert result.processed is False
    assert result.status == TransactionStatus.FAILED
    assert result.error == "Cancel failed"

    session.rollback.assert_awaited_once()