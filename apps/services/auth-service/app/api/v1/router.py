from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.usuarios import router as usuarios_router


api_router = APIRouter()

api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Autenticação"],
)

api_router.include_router(
    usuarios_router,
    prefix="/usuarios",
    tags=["Usuários"],
)