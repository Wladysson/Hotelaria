from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configurações centralizadas do Reservation Service.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = "Reservation Service"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"

    HOST: str = "0.0.0.0"
    PORT: int = 8001

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://reservation:reservation@localhost:5439/reservation",
    )

    DB_POOL_SIZE: int = Field(
        default=10,
        ge=1,
        le=100,
    )

    DB_MAX_OVERFLOW: int = Field(
        default=20,
        ge=0,
        le=100,
    )

    DB_POOL_TIMEOUT: int = Field(
        default=30,
        ge=1,
    )

    DB_POOL_RECYCLE: int = Field(
        default=1800,
        ge=60,
    )

    DB_ECHO: bool = False

    REDIS_URL: str = "redis://localhost:6379/0"

    CACHE_TTL_SECONDS: int = Field(
        default=300,
        ge=1,
    )

    DEFAULT_PAGE_SIZE: int = Field(
        default=20,
        ge=1,
    )

    MAX_PAGE_SIZE: int = Field(
        default=100,
        ge=1,
    )

    RESERVATION_HOLD_MINUTES: int = Field(
        default=15,
        ge=1,
        le=60,
    )

    RESERVATION_TIMEOUT_SECONDS: int = Field(
        default=30,
        ge=1,
    )

    CORS_ORIGINS: str = "http://localhost:5173"

    CORS_ALLOW_CREDENTIALS: bool = True

    CORS_ALLOW_METHODS: str = (
        "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    )

    CORS_ALLOW_HEADERS: str = "*"

    LOG_LEVEL: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """
    Retorna uma única instância das configurações.
    """

    return Settings()


settings = get_settings()