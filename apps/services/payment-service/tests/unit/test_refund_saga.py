from decimal import Decimal
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from src.models.refund import RefundStatus
from src.schemas.refund import RefundCreate
from src.services.refund_service import (
    RefundAlreadyProcessedError,
    RefundNotAllowedError,
    RefundServiceError,
)
from src.services.saga.refund_saga import (
    RefundSaga,
    RefundSagaCompensationError,
    RefundSagaError,
)


@pytest.fixture
def refund_service():
    return Mock()


@pytest.fixture
def refund_saga(refund_service):
    return RefundSaga(refund_service)


@pytest.fixture
def refund_data():
    return RefundCreate(
        transaction_id=uuid4(),
        reservation_id=uuid4(),
        amount=Decimal("50.00"),
        reason="customer_request",
        idempotency_key=f"refund-{uuid4()}",
        description="Reembolso de teste",
    )


def build_refund(
    *,
    status: RefundStatus,
):
    refund = Mock()

    refund.id = uuid4()
    refund.transaction_id = uuid4()
    refund.reservation_id = uuid4()
    refund.amount = Decimal("50.00")
    refund.currency = "BRL"
    refund.status = status
    refund.gateway_refund_id = "gateway-refund-001"
    refund.failure_code = None
    refund.failure_message = None

    return refund


@pytest.mark.asyncio
async def test_execute_returns_existing_refund(
    refund_saga,
    refund_service,
    refund_data,
):
    refund = build_refund(
        status=RefundStatus.SUCCEEDED,
    )

    refund_service.get_refund_by_idempotency_key = AsyncMock(
        return_value=refund,
    )

    refund_service.create_refund = AsyncMock()

    result = await refund_saga.execute(
        refund_data,
    )

    assert result is refund

    refund_service.create_refund.assert_not_awaited()


@pytest.mark.asyncio
async def test_execute_creates_new_refund(
    refund_saga,
    refund_service,
    refund_data,
):
    refund = build_refund(
        status=RefundStatus.SUCCEEDED,
    )

    refund_service.get_refund_by_idempotency_key = AsyncMock(
        return_value=None,
    )

    refund_service.create_refund = AsyncMock(
        return_value=refund,
    )

    result = await refund_saga.execute(
        refund_data,
    )

    assert result is refund

    refund_service.create_refund.assert_awaited_once_with(
        refund_data,
    )


@pytest.mark.asyncio
async def test_execute_rejects_failed_refund(
    refund_saga,
    refund_service,
    refund_data,
):
    refund = build_refund(
        status=RefundStatus.FAILED,
    )

    refund_service.get_refund_by_idempotency_key = AsyncMock(
        return_value=None,
    )

    refund_service.create_refund = AsyncMock(
        return_value=refund,
    )

    with pytest.raises(RefundSagaError) as exc_info:
        await refund_saga.execute(
            refund_data,
        )

    assert "recusou" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_execute_handles_duplicate_refund(
    refund_saga,
    refund_service,
    refund_data,
):
    existing_refund = build_refund(
        status=RefundStatus.SUCCEEDED,
    )

    refund_service.get_refund_by_idempotency_key = AsyncMock(
        side_effect=[
            None,
            existing_refund,
        ],
    )

    refund_service.create_refund = AsyncMock(
        side_effect=RefundAlreadyProcessedError(
            "Reembolso já processado."
        ),
    )

    result = await refund_saga.execute(
        refund_data,
    )

    assert result is existing_refund

    assert (
        refund_service.get_refund_by_idempotency_key.await_count
        == 2
    )


@pytest.mark.asyncio
async def test_execute_raises_when_duplicate_cannot_be_recovered(
    refund_saga,
    refund_service,
    refund_data,
):
    refund_service.get_refund_by_idempotency_key = AsyncMock(
        side_effect=[
            None,
            None,
        ],
    )

    refund_service.create_refund = AsyncMock(
        side_effect=RefundAlreadyProcessedError(
            "Reembolso já processado."
        ),
    )

    with pytest.raises(RefundSagaError) as exc_info:
        await refund_saga.execute(
            refund_data,
        )

    assert "recuperar" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_execute_handles_refund_not_allowed(
    refund_saga,
    refund_service,
    refund_data,
):
    refund_service.get_refund_by_idempotency_key = AsyncMock(
        return_value=None,
    )

    refund_service.create_refund = AsyncMock(
        side_effect=RefundNotAllowedError(
            "Reembolso não permitido."
        ),
    )

    with pytest.raises(RefundSagaError) as exc_info:
        await refund_saga.execute(
            refund_data,
        )

    assert "não permite" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_execute_handles_generic_service_error(
    refund_saga,
    refund_service,
    refund_data,
):
    refund_service.get_refund_by_idempotency_key = AsyncMock(
        return_value=None,
    )

    refund_service.create_refund = AsyncMock(
        side_effect=RefundServiceError(
            "Falha no serviço."
        ),
    )

    with pytest.raises(RefundSagaError) as exc_info:
        await refund_saga.execute(
            refund_data,
        )

    assert "fluxo" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_retry_returns_succeeded_refund(
    refund_saga,
    refund_service,
    refund_data,
):
    refund = build_refund(
        status=RefundStatus.SUCCEEDED,
    )

    refund_service.get_refund_by_idempotency_key = AsyncMock(
        return_value=refund,
    )

    result = await refund_saga.retry(
        refund_data,
    )

    assert result is refund


@pytest.mark.asyncio
async def test_retry_returns_processing_refund(
    refund_saga,
    refund_service,
    refund_data,
):
    refund = build_refund(
        status=RefundStatus.PROCESSING,
    )

    refund_service.get_refund_by_idempotency_key = AsyncMock(
        return_value=refund,
    )

    result = await refund_saga.retry(
        refund_data,
    )

    assert result is refund


@pytest.mark.asyncio
async def test_retry_executes_new_flow_when_refund_not_found(
    refund_saga,
    refund_service,
    refund_data,
):
    refund = build_refund(
        status=RefundStatus.SUCCEEDED,
    )

    refund_service.get_refund_by_idempotency_key = AsyncMock(
        return_value=None,
    )

    refund_service.create_refund = AsyncMock(
        return_value=refund,
    )

    result = await refund_saga.retry(
        refund_data,
    )

    assert result is refund

    refund_service.create_refund.assert_awaited_once_with(
        refund_data,
    )


@pytest.mark.asyncio
async def test_retry_reprocesses_failed_refund(
    refund_saga,
    refund_service,
    refund_data,
):
    failed_refund = build_refund(
        status=RefundStatus.FAILED,
    )

    successful_refund = build_refund(
        status=RefundStatus.SUCCEEDED,
    )

    refund_service.get_refund_by_idempotency_key = AsyncMock(
        side_effect=[
            failed_refund,
            failed_refund,
        ],
    )

    refund_service.create_refund = AsyncMock(
        return_value=successful_refund,
    )

    result = await refund_saga.retry(
        refund_data,
    )

    assert result is successful_refund


@pytest.mark.asyncio
async def test_get_status_success(
    refund_saga,
    refund_service,
):
    refund_id = uuid4()

    refund = build_refund(
        status=RefundStatus.PROCESSING,
    )

    refund_service.get_refund = AsyncMock(
        return_value=refund,
    )

    result = await refund_saga.get_status(
        refund_id,
    )

    assert result is refund

    refund_service.get_refund.assert_awaited_once_with(
        refund_id,
    )


@pytest.mark.asyncio
async def test_get_status_wraps_service_error(
    refund_saga,
    refund_service,
):
    refund_id = uuid4()

    refund_service.get_refund = AsyncMock(
        side_effect=RefundServiceError(
            "Reembolso não encontrado."
        ),
    )

    with pytest.raises(RefundSagaError):
        await refund_saga.get_status(
            refund_id,
        )


@pytest.mark.asyncio
async def test_handle_gateway_failure_marks_refund_as_failed(
    refund_saga,
    refund_service,
):
    refund = build_refund(
        status=RefundStatus.PROCESSING,
    )

    refund_service.get_refund = AsyncMock(
        return_value=refund,
    )

    result = await refund_saga.handle_gateway_failure(
        refund_id=refund.id,
        failure_code="gateway_timeout",
        failure_message="Timeout no gateway.",
    )

    assert result.status == RefundStatus.FAILED
    assert result.failure_code == "gateway_timeout"
    assert result.failure_message == "Timeout no gateway."


@pytest.mark.asyncio
async def test_handle_gateway_failure_preserves_succeeded_refund(
    refund_saga,
    refund_service,
):
    refund = build_refund(
        status=RefundStatus.SUCCEEDED,
    )

    refund_service.get_refund = AsyncMock(
        return_value=refund,
    )

    result = await refund_saga.handle_gateway_failure(
        refund_id=refund.id,
        failure_code="late_failure",
        failure_message="Falha tardia.",
    )

    assert result.status == RefundStatus.SUCCEEDED
    assert result.failure_code is None
    assert result.failure_message is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status",
    [
        RefundStatus.SUCCEEDED,
        RefundStatus.FAILED,
        RefundStatus.CANCELLED,
    ],
)
async def test_is_completed(
    status,
):
    refund = build_refund(
        status=status,
    )

    assert RefundSaga.is_completed(refund) is (
        status == RefundStatus.SUCCEEDED
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status",
    [
        RefundStatus.PROCESSING,
        RefundStatus.PENDING,
        RefundStatus.SUCCEEDED,
        RefundStatus.FAILED,
    ],
)
async def test_requires_follow_up(
    status,
):
    refund = build_refund(
        status=status,
    )

    assert RefundSaga.requires_follow_up(refund) is (
        status == RefundStatus.PROCESSING
    )