from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.cache import cache
from src.core.config import settings
from src.core.database import (
    close_database,
    init_database,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação.
    """

    await init_database()

    await cache.connect()

    yield

    await cache.close()

    await close_database()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.cors_allow_methods_list,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


@app.get(
    "/health",
    tags=["Health"],
    summary="Verifica a saúde do serviço",
)
async def health_check() -> dict[str, str]:
    """
    Endpoint básico de health check.

    Não depende de banco ou Redis.
    """

    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get(
    "/ready",
    tags=["Health"],
    summary="Verifica se o serviço está pronto",
)
async def readiness_check() -> dict[str, object]:
    """
    Verifica se as dependências necessárias estão disponíveis.
    """

    redis_available = await cache.health_check()

    if not redis_available:
        return {
            "status": "not_ready",
            "service": settings.APP_NAME,
            "dependencies": {
                "redis": False,
            },
        }

    return {
        "status": "ready",
        "service": settings.APP_NAME,
        "dependencies": {
            "redis": True,
        },
    }


@app.get(
    "/",
    tags=["Root"],
    summary="Informações do serviço",
)
async def root() -> dict[str, str]:
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "openapi": "/openapi.json",
    }