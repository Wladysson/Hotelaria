from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.deps import get_refund_service
from src.schemas.refund import (
    RefundCreate,
    RefundResponse,
    RefundStatusResponse,
)
from src.services.refund_service import (
    RefundAlreadyProcessedError,
    RefundNotAllowedError,
    RefundNotFoundError,
    RefundService,
    RefundServiceError,
)
from src.services.saga.refund_saga import (
    RefundSaga,
    RefundSagaError,
)


router = APIRouter()


def get_refund_saga(
    refund_service: RefundService = Depends(get_refund_service),
) -> RefundSaga:
    return RefundSaga(refund_service)


@router.post(
    "",
    response_model=RefundResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Solicita um reembolso",
    description=(
        "Cria e processa uma solicitação de reembolso "
        "através do gateway utilizado pela transação."
    ),
)
async def create_refund(
    data: RefundCreate,
    saga: RefundSaga = Depends(get_refund_saga),
) -> RefundResponse:
    try:
        refund = await saga.execute(data)

        return RefundResponse.model_validate(refund)

    except RefundAlreadyProcessedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except RefundNotAllowedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except RefundSagaError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post(
    "/retry",
    response_model=RefundResponse,
    status_code=status.HTTP_200_OK,
    summary="Reprocessa um reembolso",
    description=(
        "Reprocessa uma solicitação de reembolso utilizando "
        "a chave de idempotência para evitar duplicidade."
    ),
)
async def retry_refund(
    data: RefundCreate,
    saga: RefundSaga = Depends(get_refund_saga),
) -> RefundResponse:
    try:
        refund = await saga.retry(data)

        return RefundResponse.model_validate(refund)

    except RefundSagaError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get(
    "/{refund_id}",
    response_model=RefundResponse,
    status_code=status.HTTP_200_OK,
    summary="Consulta um reembolso",
)
async def get_refund(
    refund_id: UUID,
    saga: RefundSaga = Depends(get_refund_saga),
) -> RefundResponse:
    try:
        refund = await saga.get_status(refund_id)

        return RefundResponse.model_validate(refund)

    except RefundNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except RefundSagaError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get(
    "/{refund_id}/status",
    response_model=RefundStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Consulta o status de um reembolso",
)
async def get_refund_status(
    refund_id: UUID,
    saga: RefundSaga = Depends(get_refund_saga),
) -> RefundStatusResponse:
    try:
        refund = await saga.get_status(refund_id)

        return RefundStatusResponse(
            id=refund.id,
            transaction_id=refund.transaction_id,
            status=refund.status,
            amount=refund.amount,
            gateway_refund_id=refund.gateway_refund_id,
            failure_code=refund.failure_code,
            failure_message=refund.failure_message,
        )

    except RefundNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except RefundSagaError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc