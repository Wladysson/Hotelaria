from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text

from src.api.v1.router import api_router
from src.core.config import settings
from src.core.database import engine
from src.api.middleware.cors import setup_cors
from src.api.middleware.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    await check_database_connection()

    yield

    await engine.dispose()


async def check_database_connection() -> None:
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))


app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    debug=settings.debug,
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
    lifespan=lifespan,
)

setup_cors(app)
setup_logging(app)

app.include_router(
    api_router,
    prefix=settings.api_prefix,
)


@app.get(
    "/health",
    tags=["Health"],
    summary="Verifica a saúde do serviço",
)
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@app.get(
    "/ready",
    tags=["Health"],
    summary="Verifica se o serviço está pronto",
)
async def readiness_check() -> dict[str, str]:
    await check_database_connection()

    return {
        "status": "ready",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Os dados enviados são inválidos.",
            "details": exc.errors(),
            "path": str(request.url.path),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    if settings.debug:
        detail = str(exc)
    else:
        detail = "Ocorreu um erro interno no servidor."

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": detail,
            "path": str(request.url.path),
        },
    )