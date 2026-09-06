from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.database import close_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield

    # Shutdown
    await close_database()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Microserviço responsável pelo processamento de pagamentos, "
        "gerenciamento de transações, reembolsos e integrações "
        "com gateways de pagamento."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.cors_methods_list,
    allow_headers=settings.cors_headers_list,
)


@app.get(
    "/",
    tags=["Health"],
    summary="Verifica a disponibilidade do serviço",
)
async def root() -> dict[str, str]:
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
    }


@app.get(
    "/health",
    tags=["Health"],
    summary="Verifica a saúde da aplicação",
)
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
    }


@app.get(
    "/ready",
    tags=["Health"],
    summary="Verifica se o serviço está pronto para receber requisições",
)
async def readiness_check() -> dict[str, str]:
    return {
        "status": "ready",
        "service": settings.APP_NAME,
    }


# Routers da API serão registrados conforme os módulos forem implementados.
#
# Exemplo da estrutura final:
#
# from src.api.v1.router import api_router
#
# app.include_router(
#     api_router,
#     prefix="/api/v1",
# )