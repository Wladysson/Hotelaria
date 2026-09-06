from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.deps import (
    get_reservation_service,
    get_saga_orchestrator,
)
from src.services.reservation_service import ReservationService
from src.services.saga.saga_orchestrator import SagaOrchestrator


router = APIRouter(
    prefix="/reservations",
    tags=["Reservations"],
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma reserva",
)
async def create_reservation(
    user_id: UUID,
    hotel_id: UUID,
    check_in: date,
    check_out: date,
    guests: int = Query(
        default=1,
        ge=1,
        le=50,
    ),
    rooms: int = Query(
        default=1,
        ge=1,
        le=20,
    ),
    price_per_night: Decimal = Query(
        ...,
        gt=0,
    ),
    discount_percent: Decimal = Query(
        default=Decimal("0"),
        ge=0,
        le=100,
    ),
    tax_percent: Decimal = Query(
        default=Decimal("0"),
        ge=0,
        le=100,
    ),
    orchestrator: SagaOrchestrator = Depends(
        get_saga_orchestrator
    ),
):
    if check_out <= check_in:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A data de checkout deve ser posterior ao check-in.",
        )

    result = await orchestrator.create_booking(
        hotel_id=hotel_id,
        check_in=check_in,
        check_out=check_out,
        guests=guests,
        rooms=rooms,
        price_per_night=price_per_night,
        discount_percent=discount_percent,
        tax_percent=tax_percent,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível concluir a reserva.",
        )

    return result


@router.get(
    "",
    summary="Lista reservas",
)
async def list_reservations(
    user_id: UUID | None = None,
    hotel_id: UUID | None = None,
    reservation_status: str | None = Query(
        default=None,
        alias="status",
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    service: ReservationService = Depends(
        get_reservation_service
    ),
):
    return await service.list_reservations(
        user_id=user_id,
        hotel_id=hotel_id,
        status=reservation_status,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{reservation_id}",
    summary="Consulta uma reserva",
)
async def get_reservation(
    reservation_id: UUID,
    user_id: UUID | None = None,
    service: ReservationService = Depends(
        get_reservation_service
    ),
):
    return await service.get_reservation(
        reservation_id=reservation_id,
        user_id=user_id,
    )


@router.patch(
    "/{reservation_id}",
    summary="Atualiza uma reserva",
)
async def update_reservation(
    reservation_id: UUID,
    user_id: UUID,
    data: dict,
    service: ReservationService = Depends(
        get_reservation_service
    ),
):
    return await service.update_reservation(
        reservation_id=reservation_id,
        user_id=user_id,
        data=data,
    )


@router.post(
    "/{reservation_id}/confirm",
    summary="Confirma uma reserva",
)
async def confirm_reservation(
    reservation_id: UUID,
    user_id: UUID,
    service: ReservationService = Depends(
        get_reservation_service
    ),
):
    return await service.confirm_reservation(
        reservation_id=reservation_id,
        user_id=user_id,
    )


@router.post(
    "/{reservation_id}/guests",
    status_code=status.HTTP_201_CREATED,
    summary="Adiciona hóspede à reserva",
)
async def add_guest(
    reservation_id: UUID,
    user_id: UUID,
    data: dict,
    service: ReservationService = Depends(
        get_reservation_service
    ),
):
    return await service.add_guest(
        reservation_id=reservation_id,
        user_id=user_id,
        guest_data=data,
    )