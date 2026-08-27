from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configurações centralizadas do Hotel Service.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "Hotel Service"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "Serviço responsável pelo catálogo de hotéis, quartos, "
        "comodidades e consulta de disponibilidade."
    )

    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://hotel:hotel@localhost:5432/hotel",
        description="URL assíncrona de conexão com PostgreSQL.",
    )

    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 1800
    DATABASE_ECHO: bool = False

    REDIS_URL: str = "redis://localhost:6379/0"

    REDIS_MAX_CONNECTIONS: int = 50

    CACHE_DEFAULT_TTL: int = 300

    CACHE_HOTEL_TTL: int = 600
    CACHE_CITY_TTL: int = 1800
    CACHE_SEARCH_TTL: int = 120

    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    CORS_ALLOW_CREDENTIALS: bool = True

    CORS_ALLOW_METHODS: str = (
        "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    )

    CORS_ALLOW_HEADERS: str = "*"

    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    SEARCH_MAX_RESULTS: int = 100

    AVAILABILITY_CACHE_TTL: int = 60


    LOG_LEVEL: str = "INFO"

    REQUEST_ID_HEADER: str = "X-Request-ID"

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]

    @property
    def cors_allow_methods_list(self) -> list[str]:
        return [
            method.strip()
            for method in self.CORS_ALLOW_METHODS.split(",")
            if method.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()