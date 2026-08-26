from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(
        default="Auth Service",
        alias="APP_NAME",
    )

    app_description: str = Field(
        default="Serviço responsável por autenticação, identidade e autorização.",
        alias="APP_DESCRIPTION",
    )

    app_version: str = Field(
        default="1.0.0",
        alias="APP_VERSION",
    )

    environment: str = Field(
        default="development",
        alias="ENVIRONMENT",
    )

    debug: bool = Field(
        default=False,
        alias="DEBUG",
    )

    api_prefix: str = Field(
        default="/api/v1",
        alias="API_PREFIX",
    )

    docs_enabled: bool = Field(
        default=True,
        alias="DOCS_ENABLED",
    )

    database_url: str = Field(
        alias="DATABASE_URL",
    )

    database_pool_size: int = Field(
        default=10,
        alias="DATABASE_POOL_SIZE",
    )

    database_max_overflow: int = Field(
        default=20,
        alias="DATABASE_MAX_OVERFLOW",
    )

    database_pool_timeout: int = Field(
        default=30,
        alias="DATABASE_POOL_TIMEOUT",
    )

    database_pool_recycle: int = Field(
        default=1800,
        alias="DATABASE_POOL_RECYCLE",
    )

    jwt_secret_key: str = Field(
        alias="JWT_SECRET_KEY",
    )

    jwt_algorithm: str = Field(
        default="HS256",
        alias="JWT_ALGORITHM",
    )

    access_token_expire_minutes: int = Field(
        default=15,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )

    refresh_token_expire_days: int = Field(
        default=30,
        alias="REFRESH_TOKEN_EXPIRE_DAYS",
    )

    password_reset_token_expire_minutes: int = Field(
        default=15,
        alias="PASSWORD_RESET_TOKEN_EXPIRE_MINUTES",
    )

    email_verification_token_expire_minutes: int = Field(
        default=30,
        alias="EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES",
    )

    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        alias="CORS_ORIGINS",
    )

    cors_allow_credentials: bool = Field(
        default=True,
        alias="CORS_ALLOW_CREDENTIALS",
    )

    cors_allow_methods: str = Field(
        default="*",
        alias="CORS_ALLOW_METHODS",
    )

    cors_allow_headers: str = Field(
        default="*",
        alias="CORS_ALLOW_HEADERS",
    )

    auth_cookie_secure: bool = Field(
        default=False,
        alias="AUTH_COOKIE_SECURE",
    )

    auth_cookie_domain: str | None = Field(
        default=None,
        alias="AUTH_COOKIE_DOMAIN",
    )

    auth_cookie_samesite: str = Field(
        default="lax",
        alias="AUTH_COOKIE_SAMESITE",
    )

    login_max_attempts: int = Field(
        default=5,
        alias="LOGIN_MAX_ATTEMPTS",
    )

    login_lockout_minutes: int = Field(
        default=15,
        alias="LOGIN_LOCKOUT_MINUTES",
    )

    password_min_length: int = Field(
        default=8,
        alias="PASSWORD_MIN_LENGTH",
    )

    password_max_length: int = Field(
        default=128,
        alias="PASSWORD_MAX_LENGTH",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def database_url_async(self) -> str:
        if self.database_url.startswith("postgresql+asyncpg://"):
            return self.database_url

        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace(
                "postgresql://",
                "postgresql+asyncpg://",
                1,
            )

        if self.database_url.startswith("postgres://"):
            return self.database_url.replace(
                "postgres://",
                "postgresql+asyncpg://",
                1,
            )

        return self.database_url

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def cors_methods_list(self) -> list[str]:
        return [
            method.strip()
            for method in self.cors_allow_methods.split(",")
            if method.strip()
        ]

    @property
    def cors_headers_list(self) -> list[str]:
        return [
            header.strip()
            for header in self.cors_allow_headers.split(",")
            if header.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()