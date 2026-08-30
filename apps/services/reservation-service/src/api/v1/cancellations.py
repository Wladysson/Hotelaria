from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.deps import get_saga_orchestrator
from src.services.saga.saga_orchestrator import SagaOrchestrator


router = APIRouter(
    prefix="/cancellations",
    tags=["Cancellations"],
)


@router.post(
    "/{reservation_id}",
    summary="Cancela uma reserva",
)
async def cancel_reservation(
    reservation_id: UUID,
    reason: str | None = Query(
        default=None,
        max_length=500,
    ),
    orchestrator: SagaOrchestrator = Depends(
        get_saga_orchestrator
    ),
):
    result = await orchestrator.cancel_booking(
        reservation_id=reservation_id,
        reason=reason,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Não foi possível concluir o "
                "cancelamento da reserva."
            ),
        )

    return result