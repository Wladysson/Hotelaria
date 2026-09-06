from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from src.models.refund import RefundStatus
from src.models.transactions import (
    PaymentProvider,
    TransactionStatus,
)
from src.workers.tasks.reconciliation_tasks import (
    _detect_discrepancy,
    _normalize_external_status,
    _synchronize_transaction,
    reconcile_pending_transactions,
    reconcile_refund,
    reconcile_transaction,
)


def build_transaction(
    *,
    status: TransactionStatus,
    gateway_transaction_id: str | None = "gateway-tx-001",
):
    transaction = Mock()
    transaction.id = uuid4()
    transaction.provider = PaymentProvider.STRIPE
    transaction.status = status
    transaction.gateway_transaction_id = gateway_transaction_id
    transaction.captured_amount = Decimal("0.00")
    transaction.amount = Decimal("150.00")
    return transaction


def build_refund(
    *,
    status: RefundStatus,
    gateway_refund_id: str | None = "gateway-refund-001",
):
    refund = Mock()
    refund.id = uuid4()
    refund.status = status
    refund.gateway_refund_id = gateway_refund_id
    return refund


def build_session_context(session):
    context = Mock()
    context.__aenter__ = AsyncMock(return_value=session)
    context.__aexit__ = AsyncMock(return_value=None)
    return context


@pytest.mark.asyncio
async def test_reconcile_transaction_returns_reconciled_when_statuses_match():
    transaction = build_transaction(
        status=TransactionStatus.SUCCEEDED,
    )

    session = AsyncMock()
    session.get = AsyncMock(return_value=transaction)

    gateway = Mock()
    gateway.get_payment = AsyncMock(
        return_value={
            "status": "succeeded",
            "captured_amount": Decimal("150.00"),
        },
    )

    gateway_factory = Mock()
    gateway_factory.get_gateway.return_value = gateway

    context = build_session_context(session)

    with patch(
        "src.workers.tasks.reconciliation_tasks.AsyncSessionLocal",
        return_value=context,
    ):
        with patch(
            "src.workers.tasks.reconciliation_tasks.GatewayFactory",
            return_value=gateway_factory,
        ):
            result = await reconcile_transaction(transaction.id)

    assert result.transaction_id == transaction.id
    assert result.internal_status == TransactionStatus.SUCCEEDED
    assert result.external_status == "succeeded"
    assert result.reconciled is True
    assert result.discrepancy is None

    gateway.get_payment.assert_awaited_once_with(
        gateway_transaction_id="gateway-tx-001",
    )
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_reconcile_transaction_synchronizes_authorized_to_succeeded():
    transaction = build_transaction(
        status=TransactionStatus.AUTHORIZED,
    )

    session = AsyncMock()
    session.get = AsyncMock(return_value=transaction)

    gateway = Mock()
    gateway.get_payment = AsyncMock(
        return_value={
            "status": "succeeded",
            "captured_amount": Decimal("150.00"),
        },
    )

    gateway_factory = Mock()
    gateway_factory.get_gateway.return_value = gateway

    context = build_session_context(session)

    with patch(
        "src.workers.tasks.reconciliation_tasks.AsyncSessionLocal",
        return_value=context,
    ):
        with patch(
            "src.workers.tasks.reconciliation_tasks.GatewayFactory",
            return_value=gateway_factory,
        ):
            result = await reconcile_transaction(transaction.id)

    assert result.reconciled is True
    assert transaction.status == TransactionStatus.SUCCEEDED
    assert transaction.captured_amount == Decimal("150.00")
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_reconcile_transaction_synchronizes_processing_to_failed():
    transaction = build_transaction(
        status=TransactionStatus.PROCESSING,
    )

    session = AsyncMock()
    session.get = AsyncMock(return_value=transaction)

    gateway = Mock()
    gateway.get_payment = AsyncMock(
        return_value={
            "status": "failed",
        },
    )

    gateway_factory = Mock()
    gateway_factory.get_gateway.return_value = gateway

    context = build_session_context(session)

    with patch(
        "src.workers.tasks.reconciliation_tasks.AsyncSessionLocal",
        return_value=context,
    ):
        with patch(
            "src.workers.tasks.reconciliation_tasks.GatewayFactory",
            return_value=gateway_factory,
        ):
            result = await reconcile_transaction(transaction.id)

    assert result.reconciled is True
    assert result.internal_status == TransactionStatus.FAILED
    assert transaction.status == TransactionStatus.FAILED
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_reconcile_transaction_synchronizes_processing_to_cancelled():
    transaction = build_transaction(
        status=TransactionStatus.PROCESSING,
    )

    session = AsyncMock()
    session.get = AsyncMock(return_value=transaction)

    gateway = Mock()
    gateway.get_payment = AsyncMock(
        return_value={
            "status": "cancelled",
        },
    )

    gateway_factory = Mock()
    gateway_factory.get_gateway.return_value = gateway

    context = build_session_context(session)

    with patch(
        "src.workers.tasks.reconciliation_tasks.AsyncSessionLocal",
        return_value=context,
    ):
        with patch(
            "src.workers.tasks.reconciliation_tasks.GatewayFactory",
            return_value=gateway_factory,
        ):
            result = await reconcile_transaction(transaction.id)

    assert result.reconciled is True
    assert transaction.status == TransactionStatus.CANCELLED
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_reconcile_transaction_detects_terminal_status_discrepancy():
    transaction = build_transaction(
        status=TransactionStatus.SUCCEEDED,
    )

    session = AsyncMock()
    session.get = AsyncMock(return_value=transaction)

    gateway = Mock()
    gateway.get_payment = AsyncMock(
        return_value={
            "status": "failed",
        },
    )

    gateway_factory = Mock()
    gateway_factory.get_gateway.return_value = gateway

    context = build_session_context(session)

    with patch(
        "src.workers.tasks.reconciliation_tasks.AsyncSessionLocal",
        return_value=context,
    ):
        with patch(
            "src.workers.tasks.reconciliation_tasks.GatewayFactory",
            return_value=gateway_factory,
        ):
            result = await reconcile_transaction(transaction.id)

    assert result.reconciled is False
    assert result.discrepancy is not None
    assert "terminal" in result.discrepancy.lower()
    assert transaction.status == TransactionStatus.SUCCEEDED
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_reconcile_transaction_raises_when_transaction_not_found():
    transaction_id = uuid4()

    session = AsyncMock()
    session.get = AsyncMock(return_value=None)

    context = build_session_context(session)

    with patch(
        "src.workers.tasks.reconciliation_tasks.AsyncSessionLocal",
        return_value=context,
    ):
        with pytest.raises(
            ValueError,
            match="Transação não encontrada",
        ):
            await reconcile_transaction(transaction_id)


@pytest.mark.asyncio
async def test_reconcile_transaction_raises_without_provider():
    transaction = build_transaction(
        status=TransactionStatus.PROCESSING,
    )
    transaction.provider = None

    session = AsyncMock()
    session.get = AsyncMock(return_value=transaction)

    context = build_session_context(session)

    with patch(
        "src.workers.tasks.reconciliation_tasks.AsyncSessionLocal",
        return_value=context,
    ):
        with pytest.raises(
            ValueError,
            match="provedor de pagamento",
        ):
            await reconcile_transaction(transaction.id)


@pytest.mark.asyncio
async def test_reconcile_transaction_raises_without_gateway_transaction_id():
    transaction = build_transaction(
        status=TransactionStatus.PROCESSING,
        gateway_transaction_id=None,
    )

    session = AsyncMock()
    session.get = AsyncMock(return_value=transaction)

    context = build_session_context(session)

    with patch(
        "src.workers.tasks.reconciliation_tasks.AsyncSessionLocal",
        return_value=context,
    ):
        with pytest.raises(
            ValueError,
            match="identificador externo",
        ):
            await reconcile_transaction(transaction.id)


@pytest.mark.asyncio
async def test_reconcile_pending_transactions_processes_pending_transactions():
    first_transaction = build_transaction(
        status=TransactionStatus.PENDING,
    )
    second_transaction = build_transaction(
        status=TransactionStatus.PROCESSING,
    )

    session = AsyncMock()

    execute_result = Mock()
    execute_result.scalars.return_value.all.return_value = [
        first_transaction,
        second_transaction,
    ]

    session.execute = AsyncMock(return_value=execute_result)

    context = build_session_context(session)

    first_result = Mock(
        transaction_id=first_transaction.id,
        internal_status=TransactionStatus.SUCCEEDED,
        external_status="succeeded",
        reconciled=True,
        discrepancy=None,
    )

    second_result = Mock(
        transaction_id=second_transaction.id,
        internal_status=TransactionStatus.FAILED,
        external_status="failed",
        reconciled=True,
        discrepancy=None,
    )

    with patch(
        "src.workers.tasks.reconciliation_tasks.AsyncSessionLocal",
        return_value=context,
    ):
        with patch(
            "src.workers.tasks.reconciliation_tasks.reconcile_transaction",
            new_callable=AsyncMock,
            side_effect=[
                first_result,
                second_result,
            ],
        ) as reconcile_mock:
            results = await reconcile_pending_transactions(limit=10)

    assert len(results) == 2
    assert results[0] == first_result
    assert results[1] == second_result

    assert reconcile_mock.await_count == 2
    reconcile_mock.assert_any_await(first_transaction.id)
    reconcile_mock.assert_any_await(second_transaction.id)


@pytest.mark.asyncio
async def test_reconcile_pending_transactions_handles_individual_failure():
    transaction = build_transaction(
        status=TransactionStatus.PROCESSING,
    )

    session = AsyncMock()

    execute_result = Mock()
    execute_result.scalars.return_value.all.return_value = [
        transaction,
    ]

    session.execute = AsyncMock(return_value=execute_result)

    context = build_session_context(session)

    with patch(
        "src.workers.tasks.reconciliation_tasks.AsyncSessionLocal",
        return_value=context,
    ):
        with patch(
            "src.workers.tasks.reconciliation_tasks.reconcile_transaction",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Gateway unavailable"),
        ):
            results = await reconcile_pending_transactions(limit=10)

    assert len(results) == 1
    assert results[0].transaction_id == transaction.id
    assert results[0].reconciled is False
    assert results[0].external_status == "unknown"
    assert results[0].discrepancy == "Gateway unavailable"


@pytest.mark.asyncio
async def test_reconcile_pending_transactions_rejects_invalid_limit():
    with pytest.raises(
        ValueError,
        match="maior que zero",
    ):
        await reconcile_pending_transactions(limit=0)


@pytest.mark.asyncio
async def test_reconcile_pending_transactions_rejects_limit_above_maximum():
    with pytest.raises(
        ValueError,
        match="máximo",
    ):
        await reconcile_pending_transactions(limit=1001)


@pytest.mark.asyncio
async def test_reconcile_refund_returns_true_for_succeeded_refund():
    refund = build_refund(
        status=RefundStatus.SUCCEEDED,
    )

    session = AsyncMock()
    session.get = AsyncMock(return_value=refund)

    context = build_session_context(session)

    with patch(
        "src.workers.tasks.reconciliation_tasks.AsyncSessionLocal",
        return_value=context,
    ):
        result = await reconcile_refund(refund.id)

    assert result is True


@pytest.mark.asyncio
async def test_reconcile_refund_returns_false_without_gateway_refund_id():
    refund = build_refund(
        status=RefundStatus.PROCESSING,
        gateway_refund_id=None,
    )

    session = AsyncMock()
    session.get = AsyncMock(return_value=refund)

    context = build_session_context(session)

    with patch(
        "src.workers.tasks.reconciliation_tasks.AsyncSessionLocal",
        return_value=context,
    ):
        result = await reconcile_refund(refund.id)

    assert result is False


@pytest.mark.asyncio
async def test_reconcile_refund_returns_true_for_processing_refund():
    refund = build_refund(
        status=RefundStatus.PROCESSING,
    )

    session = AsyncMock()
    session.get = AsyncMock(return_value=refund)

    context = build_session_context(session)

    with patch(
        "src.workers.tasks.reconciliation_tasks.AsyncSessionLocal",
        return_value=context,
    ):
        result = await reconcile_refund(refund.id)

    assert result is True


@pytest.mark.asyncio
async def test_reconcile_refund_returns_false_for_pending_refund():
    refund = build_refund(
        status=RefundStatus.PENDING,
    )

    session = AsyncMock()
    session.get = AsyncMock(return_value=refund)

    context = build_session_context(session)

    with patch(
        "src.workers.tasks.reconciliation_tasks.AsyncSessionLocal",
        return_value=context,
    ):
        result = await reconcile_refund(refund.id)

    assert result is False


@pytest.mark.asyncio
async def test_reconcile_refund_raises_when_refund_not_found():
    refund_id = uuid4()

    session = AsyncMock()
    session.get = AsyncMock(return_value=None)

    context = build_session_context(session)

    with patch(
        "src.workers.tasks.reconciliation_tasks.AsyncSessionLocal",
        return_value=context,
    ):
        with pytest.raises(
            ValueError,
            match="Reembolso não encontrado",
        ):
            await reconcile_refund(refund_id)


@pytest.mark.parametrize(
    ("external_status", "expected_status"),
    [
        ("succeeded", TransactionStatus.SUCCEEDED),
        ("paid", TransactionStatus.SUCCEEDED),
        ("captured", TransactionStatus.SUCCEEDED),
        ("completed", TransactionStatus.SUCCEEDED),
        ("authorized", TransactionStatus.AUTHORIZED),
        ("requires_capture", TransactionStatus.AUTHORIZED),
        ("failed", TransactionStatus.FAILED),
        ("declined", TransactionStatus.FAILED),
        ("rejected", TransactionStatus.FAILED),
        ("cancelled", TransactionStatus.CANCELLED),
        ("canceled", TransactionStatus.CANCELLED),
        ("processing", TransactionStatus.PROCESSING),
        ("pending", TransactionStatus.PROCESSING),
        ("requires_action", TransactionStatus.PROCESSING),
    ],
)
def test_normalize_external_status(
    external_status,
    expected_status,
):
    assert _normalize_external_status(
        external_status
    ) == expected_status


@pytest.mark.parametrize(
    ("internal_status", "external_status", "expected"),
    [
        (
            TransactionStatus.SUCCEEDED,
            TransactionStatus.SUCCEEDED,
            None,
        ),
        (
            TransactionStatus.AUTHORIZED,
            TransactionStatus.SUCCEEDED,
            None,
        ),
        (
            TransactionStatus.PROCESSING,
            TransactionStatus.SUCCEEDED,
            None,
        ),
        (
            TransactionStatus.PROCESSING,
            TransactionStatus.FAILED,
            None,
        ),
        (
            TransactionStatus.PROCESSING,
            TransactionStatus.CANCELLED,
            None,
        ),
        (
            TransactionStatus.SUCCEEDED,
            TransactionStatus.FAILED,
            "Estado terminal interno divergente do estado retornado pelo gateway.",
        ),
        (
            TransactionStatus.FAILED,
            TransactionStatus.SUCCEEDED,
            "Estado terminal interno divergente do estado retornado pelo gateway.",
        ),
    ],
)
def test_detect_discrepancy(
    internal_status,
    external_status,
    expected,
):
    assert (
        _detect_discrepancy(
            internal_status=internal_status,
            external_status=external_status,
        )
        == expected
    )


def test_synchronize_transaction_updates_status_and_captured_amount():
    transaction = build_transaction(
        status=TransactionStatus.PROCESSING,
    )

    _synchronize_transaction(
        transaction=transaction,
        gateway_response={
            "status": "succeeded",
            "captured_amount": Decimal("150.00"),
        },
        external_status=TransactionStatus.SUCCEEDED,
    )

    assert transaction.status == TransactionStatus.SUCCEEDED
    assert transaction.captured_amount == Decimal("150.00")


def test_synchronize_transaction_without_captured_amount():
    transaction = build_transaction(
        status=TransactionStatus.PROCESSING,
    )

    _synchronize_transaction(
        transaction=transaction,
        gateway_response={
            "status": "succeeded",
        },
        external_status=TransactionStatus.SUCCEEDED,
    )

    assert transaction.status == TransactionStatus.SUCCEEDED
    assert transaction.captured_amount == Decimal("0.00")