from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.database import (
    check_database_connection,
    close_database,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Gerencia o ciclo de vida da aplicação.

    O banco é validado durante o startup e o pool de conexões
    é encerrado corretamente durante o shutdown.
    """

    await check_database_connection()

    yield

    await close_database()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Microsserviço responsável pelo gerenciamento de reservas "
        "da plataforma de hotelaria."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in settings.CORS_ORIGINS.split(",")
        if origin.strip()
    ],
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=[
        method.strip()
        for method in settings.CORS_ALLOW_METHODS.split(",")
        if method.strip()
    ],
    allow_headers=[
        header.strip()
        for header in settings.CORS_ALLOW_HEADERS.split(",")
        if header.strip()
    ],
)


@app.get(
    "/",
    status_code=status.HTTP_200_OK,
    tags=["System"],
    summary="Informações do serviço",
)
async def root() -> dict[str, str]:
    """
    Retorna informações básicas do Reservation Service.
    """

    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "running",
    }


@app.get(
    "/health",
    status_code=status.HTTP_200_OK,
    tags=["Health"],
    summary="Health check geral",
)
async def health() -> dict[str, str]:
    """
    Verifica se o serviço está em execução.
    """

    return {
        "status": "healthy",
        "service": settings.APP_NAME,
    }


@app.get(
    "/health/live",
    status_code=status.HTTP_200_OK,
    tags=["Health"],
    summary="Liveness probe",
)
async def liveness() -> dict[str, str]:
    """
    Endpoint utilizado pelo Kubernetes para verificar
    se o processo da aplicação está ativo.
    """

    return {
        "status": "alive",
    }


@app.get(
    "/health/ready",
    status_code=status.HTTP_200_OK,
    tags=["Health"],
    summary="Readiness probe",
)
async def readiness() -> dict[str, str]:
    """
    Verifica se a aplicação está pronta para receber tráfego.

    A disponibilidade do PostgreSQL é validada antes de
    considerar o serviço pronto.
    """

    await check_database_connection()

    return {
        "status": "ready",
        "database": "connected",
    }


@app.get(
    "/health/database",
    status_code=status.HTTP_200_OK,
    tags=["Health"],
    summary="Health check do PostgreSQL",
)
async def database_health() -> dict[str, str]:
    """
    Verifica exclusivamente a conectividade com o PostgreSQL.
    """

    await check_database_connection()

    return {
        "status": "healthy",
        "database": "connected",
    }