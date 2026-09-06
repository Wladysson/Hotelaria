from fastapi import APIRouter

from src.api.v1.cancellations import router as cancellations_router
from src.api.v1.holds import router as holds_router
from src.api.v1.reservations import router as reservations_router


router = APIRouter(
    prefix="/api/v1",
)


router.include_router(
    reservations_router,
)

router.include_router(
    holds_router,
)

router.include_router(
    cancellations_router,
)