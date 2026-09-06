from datetime import date, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.deps import get_hold_repository
from src.repositories.hold_repository import HoldRepository

router = APIRouter(
    prefix="/holds",
    tags=["Holds"],
)

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Cria um hold de inventário",
)
async def create_hold(
    user_id: UUID,
    hotel_id: UUID,
    check_in: date,
    check_out: date,
    rooms: int = Query(
        default=1,
        ge=1,
        le=20,
    ),
    expiration_minutes: int = Query(
        default=15,
        ge=1,
        le=60,
    ),
    repository: HoldRepository = Depends(
        get_hold_repository
    ),
):
    if check_out <= check_in:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A data de checkout deve ser posterior ao check-in.",
        )

    expires_at = datetime.utcnow() + timedelta(
        minutes=expiration_minutes
    )

    hold_data = {
        "id": uuid4(),
        "user_id": user_id,
        "hotel_id": hotel_id,
        "check_in": check_in,
        "check_out": check_out,
        "rooms": rooms,
        "expires_at": expires_at,
    }

    return await repository.create(
        data=hold_data,
    )


@router.get(
    "/{hold_id}",
    summary="Consulta um hold",
)
async def get_hold(
    hold_id: UUID,
    repository: HoldRepository = Depends(
        get_hold_repository
    ),
):
    hold = await repository.get_by_id(
        hold_id
    )

    if hold is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hold não encontrado.",
        )

    return hold


@router.delete(
    "/{hold_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Libera um hold",
)
async def release_hold(
    hold_id: UUID,
    repository: HoldRepository = Depends(
        get_hold_repository
    ),
):
    hold = await repository.get_by_id(
        hold_id
    )

    if hold is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hold não encontrado.",
        )

    await repository.release(
        hold_id
    )