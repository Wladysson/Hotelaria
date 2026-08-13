from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.deps import get_payment_service
from src.core.dependencies import pagination_params
from src.models.transactions import TransactionStatus
from src.schemas.transactions import (
    TransactionListResponse,
    TransactionResponse,
)
from src.services.payment_service import (
    PaymentService,
    PaymentServiceError,
    TransactionNotFoundError,
)


router = APIRouter()


def _to_transaction_response(transaction) -> TransactionResponse:
    return TransactionResponse.model_validate(transaction)


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
    status_code=status.HTTP_200_OK,
    summary="Consulta uma transação",
    description="Retorna os dados completos de uma transação de pagamento.",
)
async def get_transaction(
    transaction_id: UUID,
    payment_service: PaymentService = Depends(get_payment_service),
) -> TransactionResponse:
    try:
        transaction = await payment_service.get_payment(
            transaction_id
        )

        return _to_transaction_response(transaction)

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


@router.get(
    "/customer/{customer_id}",
    response_model=TransactionListResponse,
    status_code=status.HTTP_200_OK,
    summary="Lista transações de um cliente",
)
async def list_customer_transactions(
    customer_id: UUID,
    pagination: dict[str, int] = Depends(pagination_params),
    payment_service: PaymentService = Depends(get_payment_service),
) -> TransactionListResponse:
    transactions = (
        await payment_service.transaction_repository.list_by_customer(
            customer_id,
            offset=pagination["offset"],
            limit=pagination["limit"],
        )
    )

    total = await payment_service.transaction_repository.count_by_customer(
        customer_id
    )

    pages = (total + pagination["size"] - 1) // pagination["size"]

    return TransactionListResponse(
        items=[
            _to_transaction_response(transaction)
            for transaction in transactions
        ],
        total=total,
        page=pagination["page"],
        size=pagination["size"],
        pages=pages,
    )


@router.get(
    "/reservation/{reservation_id}",
    response_model=TransactionListResponse,
    status_code=status.HTTP_200_OK,
    summary="Lista transações de uma reserva",
)
async def list_reservation_transactions(
    reservation_id: UUID,
    pagination: dict[str, int] = Depends(pagination_params),
    payment_service: PaymentService = Depends(get_payment_service),
) -> TransactionListResponse:
    transactions = (
        await payment_service.transaction_repository.list_by_reservation(
            reservation_id,
            offset=pagination["offset"],
            limit=pagination["limit"],
        )
    )

    total = (
        await payment_service.transaction_repository.count_by_reservation(
            reservation_id
        )
    )

    pages = (total + pagination["size"] - 1) // pagination["size"]

    return TransactionListResponse(
        items=[
            _to_transaction_response(transaction)
            for transaction in transactions
        ],
        total=total,
        page=pagination["page"],
        size=pagination["size"],
        pages=pages,
    )


@router.get(
    "/status/{transaction_status}",
    response_model=TransactionListResponse,
    status_code=status.HTTP_200_OK,
    summary="Lista transações por status",
)
async def list_transactions_by_status(
    transaction_status: TransactionStatus,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    payment_service: PaymentService = Depends(get_payment_service),
) -> TransactionListResponse:
    offset = (page - 1) * size

    transactions = (
        await payment_service.transaction_repository.list_by_status(
            transaction_status,
            offset=offset,
            limit=size,
        )
    )

    # A contagem por status ainda pode ser adicionada ao repository
    # quando a consulta administrativa for expandida.
    total = len(transactions)

    pages = (total + size - 1) // size if total else 0

    return TransactionListResponse(
        items=[
            _to_transaction_response(transaction)
            for transaction in transactions
        ],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )