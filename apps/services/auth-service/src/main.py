from fastapi import FastAPI

app = FastAPI(
    title="Hotel Reservation - Auth Service",
    description="Serviço responsável por autenticação, usuários, roles e permissões.",
    version="1.0.0",
)


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    return {
        "status": "UP",
        "service": "auth-service",
    }