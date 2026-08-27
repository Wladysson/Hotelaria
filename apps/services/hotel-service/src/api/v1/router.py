from fastapi import APIRouter

from src.api.v1.cities import router as cities_router
from src.api.v1.hotels import router as hotels_router

router = APIRouter(
    prefix="/api/v1",
)

router.include_router(
    cities_router,
)

router.include_router(
    hotels_router,
)