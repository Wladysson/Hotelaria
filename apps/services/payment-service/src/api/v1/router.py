from fastapi import APIRouter

from src.api.v1.payments import router as payments_router
from src.api.v1.refund import router as refunds_router
from src.api.v1.transactions import router as transactions_router


api_router = APIRouter()


api_router.include_router(
    payments_router,
    prefix="/payments",
    tags=["Payments"],
)

api_router.include_router(
    transactions_router,
    prefix="/transactions",
    tags=["Transactions"],
)

api_router.include_router(
    refunds_router,
    prefix="/refund",
    tags=["Refund"],
)