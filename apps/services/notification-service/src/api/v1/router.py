from fastapi import APIRouter

router = APIRouter(
    prefix="/api/v1",
)


@router.get(
    "/health",
    tags=["Health"],
    summary="Verifica a saúde da API v1",
)
async def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "version": "v1",
    }