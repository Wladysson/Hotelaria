from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from src.models.refund import RefundStatus
from src.workers.tasks.refund_tasks import (
    cancel_pending_refund,
    process_refund,
    retry_refund,
)


def build_refund(
    *,
    status: RefundStatus,
):
    refund = Mock()

    refund.id = uuid4()
    refund.status = status
    refund.amount = Decimal("50.00")
    refund.gateway_refund_id = "gateway-refund-001"

    return refund


def build_session_context(session):
    context = Mock()
    context.__aenter__ = AsyncMock(
        return_value=session,
    )
    context.__aexit__ = AsyncMock(
        return_value=None,
    )
    return context


@pytest.mark.asyncio
async def test_process_refund_returns_failed_when_refund_not_found():
    session = AsyncMock()
    session.get = AsyncMock(
        return_value=None,
    )

    context = build_session_context(session)

    refund_id = uuid4()

    with patch(
        "src.workers.tasks.refund_tasks.AsyncSessionLocal",
        return_value=context,
    ):
        result = await process_refund(
            refund_id,
        )

    assert result.refund_id == refund_id
    assert result.status == RefundStatus.FAILED
    assert result.processed is False
    assert result.error == "Reembolso não encontrado."


@pytest.mark.asyncio
async def test_process_refund_ignores_succeeded_refund():
    refund = build_refund(
        status=RefundStatus.SUCCEEDED,
    )

    session = AsyncMock()
    session.get = AsyncMock(
        return_value=refund,
    )

    context = build_session_context(session)

    with patch(
        "src.workers.tasks.refund_tasks.AsyncSessionLocal",
        return_value=context,
    ):
        result = await process_refund(
            refund.id,
        )

    assert result.refund_id == refund.id
    assert result.status == RefundStatus.SUCCEEDED
    assert result.processed is False

    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_process_refund_ignores_cancelled_refund():
    refund = build_refund(
        status=RefundStatus.CANCELLED,
    )

    session = AsyncMock()
    session.get = AsyncMock(
        return_value=refund,
    )

    context = build_session_context(session)

    with patch(
        "src.workers.tasks.refund_tasks.AsyncSessionLocal",
        return_value=context,
    ):
        result = await process_refund(
            refund.id,
        )

    assert result.status == RefundStatus.CANCELLED
    assert result.processed is False


@pytest.mark.asyncio
async def test_process_refund_ignores_already_failed_refund():
    refund = build_refund(
        status=RefundStatus.FAILED,
    )

    session = AsyncMock()
    session.get = AsyncMock(
        return_value=refund,
    )

    context = build_session_context(session)

    with patch(
        "src.workers.tasks.refund_tasks.AsyncSessionLocal",
        return_value=context,
    ):
        result = await process_refund(
            refund.id,
        )

    assert result.status == RefundStatus.FAILED
    assert result.processed is False


@pytest.mark.asyncio
async def test_process_refund_marks_pending_refund_as_processing():
    refund = build_refund(
        status=RefundStatus.PENDING,
    )

    session = AsyncMock()
    session.get = AsyncMock(
        return_value=refund,
    )

    context = build_session_context(session)

    with patch(
        "src.workers.tasks.refund_tasks.AsyncSessionLocal",
        return_value=context,
    ):
        result = await process_refund(
            refund.id,
        )

    assert refund.status == RefundStatus.PROCESSING
    assert result.status == RefundStatus.PROCESSING
    assert result.processed is True

    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_refund_marks_processing_refund_as_processing():
    refund = build_refund(
        status=RefundStatus.PROCESSING,
    )

    session = AsyncMock()
    session.get = AsyncMock(
        return_value=refund,
    )

    context = build_session_context(session)

    with patch(
        "src.workers.tasks.refund_tasks.AsyncSessionLocal",
        return_value=context,
    ):
        result = await process_refund(
            refund.id,
        )

    assert refund.status == RefundStatus.PROCESSING
    assert result.processed is True

    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_refund_rolls_back_on_error():
    refund = build_refund(
        status=RefundStatus.PENDING,
    )

    session = AsyncMock()
    session.get = AsyncMock(
        return_value=refund,
    )
    session.commit.side_effect = RuntimeError(
        "Database error"
    )

    context = build_session_context(session)

    with patch(
        "src.workers.tasks.refund_tasks.AsyncSessionLocal",
        return_value=context,
    ):
        result = await process_refund(
            refund.id,
        )

    assert result.processed is False
    assert result.status == RefundStatus.FAILED
    assert result.error == "Database error"

    session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_retry_refund_returns_failed_when_refund_not_found():
    refund_id = uuid4()

    session = AsyncMock()
    session.get = AsyncMock(
        return_value=None,
    )

    context = build_session_context(session)

    with patch(
        "src.workers.tasks.refund_tasks.AsyncSessionLocal",
        return_value=context,
    ):
        result = await retry_refund(
            refund_id,
        )

    assert result.refund_id == refund_id
    assert result.status == RefundStatus.FAILED
    assert result.processed is False
    assert result.error == "Reembolso não encontrado."


@pytest.mark.asyncio
async def test_retry_refund_ignores_succeeded_refund():
    refund = build_refund(
        status=RefundStatus.SUCCEEDED,
    )

    session = AsyncMock()
    session.get = AsyncMock(
        return_value=refund,
    )

    context = build_session_context(session)

    with patch(
        "src.workers.tasks.refund_tasks.AsyncSessionLocal",
        return_value=context,
    ):
        result = await retry_refund(
            refund.id,
        )

    assert result.status == RefundStatus.SUCCEEDED
    assert result.processed is False

    session.commit.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status",
    [
        RefundStatus.PENDING,
        RefundStatus.PROCESSING,
        RefundStatus.FAILED,
        RefundStatus.CANCELLED,
    ],
)
async def test_retry_refund_moves_retryable_refund_to_processing(
    status,
):
    refund = build_refund(
        status=status,
    )

    session = AsyncMock()
    session.get = AsyncMock(
        return_value=refund,
    )

    context = build_session_context(session)

    with patch(
        "src.workers.tasks.refund_tasks.AsyncSessionLocal",
        return_value=context,
    ):
        result = await retry_refund(
            refund.id,
        )

    assert refund.status == RefundStatus.PROCESSING
    assert result.status == RefundStatus.PROCESSING
    assert result.processed is True

    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_retry_refund_propagates_database_error():
    refund = build_refund(
        status=RefundStatus.FAILED,
    )

    session = AsyncMock()
    session.get = AsyncMock(
        return_value=refund,
    )
    session.commit.side_effect = RuntimeError(
        "Database unavailable"
    )

    context = build_session_context(session)

    with patch(
        "src.workers.tasks.refund_tasks.AsyncSessionLocal",
        return_value=context,
    ):
        with pytest.raises(
            RuntimeError,
            match="Database unavailable",
        ):
            await retry_refund(
                refund.id,
            )


@pytest.mark.asyncio
async def test_cancel_pending_refund_returns_not_found():
    refund_id = uuid4()

    session = AsyncMock()
    session.get = AsyncMock(
        return_value=None,
    )

    context = build_session_context(session)

    with patch(
        "src.workers.tasks.refund_tasks.AsyncSessionLocal",
        return_value=context,
    ):
        result = await cancel_pending_refund(
            refund_id,
        )

    assert result.refund_id == refund_id
    assert result.status == RefundStatus.FAILED
    assert result.processed is False
    assert result.error == "Reembolso não encontrado."


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status",
    [
        RefundStatus.SUCCEEDED,
        RefundStatus.FAILED,
        RefundStatus.CANCELLED,
    ],
)
async def test_cancel_pending_refund_ignores_terminal_refund(
    status,
):
    refund = build_refund(
        status=status,
    )

    session = AsyncMock()
    session.get = AsyncMock(
        return_value=refund,
    )

    context = build_session_context(session)

    with patch(
        "src.workers.tasks.refund_tasks.AsyncSessionLocal",
        return_value=context,
    ):
        result = await cancel_pending_refund(
            refund.id,
        )

    assert result.status == status
    assert result.processed is False

    session.commit.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status",
    [
        RefundStatus.PENDING,
        RefundStatus.PROCESSING,
    ],
)
async def test_cancel_pending_refund_success(
    status,
):
    refund = build_refund(
        status=status,
    )

    session = AsyncMock()
    session.get = AsyncMock(
        return_value=refund,
    )

    context = build_session_context(session)

    with patch(
        "src.workers.tasks.refund_tasks.AsyncSessionLocal",
        return_value=context,
    ):
        result = await cancel_pending_refund(
            refund.id,
        )

    assert refund.status == RefundStatus.CANCELLED
    assert result.status == RefundStatus.CANCELLED
    assert result.processed is True

    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_cancel_pending_refund_handles_database_error():
    refund = build_refund(
        status=RefundStatus.PENDING,
    )

    session = AsyncMock()
    session.get = AsyncMock(
        return_value=refund,
    )
    session.commit.side_effect = RuntimeError(
        "Database error"
    )

    context = build_session_context(session)

    with patch(
        "src.workers.tasks.refund_tasks.AsyncSessionLocal",
        return_value=context,
    ):
        with pytest.raises(
            RuntimeError,
            match="Database error",
        ):
            await cancel_pending_refund(
                refund.id,
            )