from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError

from src.api.deps import get_payment_service
from src.models.transactions import TransactionStatus
from src.schemas.payment import (
    PaymentCancelRequest,
    PaymentCaptureRequest,
    PaymentCreate,
    PaymentResponse,
)
from src.services.payment_service import (
    InvalidTransactionStateError,
    PaymentAlreadyProcessedError,
    PaymentMethodNotFoundError,
    PaymentService,
    PaymentServiceError,
    TransactionNotFoundError,
)
from src.services.saga.payment_saga import (
    PaymentSaga,
    PaymentSagaError,
)


router = APIRouter()


def get_payment_saga(
    payment_service: PaymentService = Depends(get_payment_service),
) -> PaymentSaga:
    return PaymentSaga(payment_service)


def _to_payment_response(transaction) -> PaymentResponse:
    return PaymentResponse(
        transaction_id=transaction.id,
        reservation_id=transaction.reservation_id,
        customer_id=transaction.customer_id,
        amount=transaction.amount,
        currency=transaction.currency,
        provider=transaction.provider,
        status=transaction.status.value,
        gateway_transaction_id=transaction.gateway_transaction_id,
        requires_capture=transaction.requires_capture,
        captured_amount=transaction.captured_amount,
    )


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Processa um pagamento",
    description=(
        "Cria e processa uma transação de pagamento através "
        "do gateway selecionado."
    ),
)
async def create_payment(
    data: PaymentCreate,
    saga: PaymentSaga = Depends(get_payment_saga),
) -> PaymentResponse:
    try:
        transaction = await saga.execute(data)

        return _to_payment_response(transaction)

    except PaymentAlreadyProcessedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except PaymentMethodNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except PaymentSagaError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível processar a operação de forma idempotente.",
        ) from exc


@router.post(
    "/{transaction_id}/capture",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
    summary="Captura um pagamento autorizado",
)
async def capture_payment(
    transaction_id: UUID,
    data: PaymentCaptureRequest | None = None,
    saga: PaymentSaga = Depends(get_payment_saga),
) -> PaymentResponse:
    amount = data.amount if data else None

    try:
        transaction = await saga.capture(
            transaction_id=transaction_id,
            amount=amount,
        )

        return _to_payment_response(transaction)

    except TransactionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except InvalidTransactionStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except PaymentSagaError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post(
    "/{transaction_id}/cancel",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancela um pagamento",
)
async def cancel_payment(
    transaction_id: UUID,
    data: PaymentCancelRequest | None = None,
    saga: PaymentSaga = Depends(get_payment_saga),
) -> PaymentResponse:
    try:
        transaction = await saga.cancel(
            transaction_id=transaction_id,
        )

        return _to_payment_response(transaction)

    except TransactionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except InvalidTransactionStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except PaymentSagaError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get(
    "/{transaction_id}",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
    summary="Consulta um pagamento",
)
async def get_payment(
    transaction_id: UUID,
    payment_service: PaymentService = Depends(get_payment_service),
) -> PaymentResponse:
    try:
        transaction = await payment_service.get_payment(
            transaction_id,
        )

        return _to_payment_response(transaction)

    except TransactionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except PaymentServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc