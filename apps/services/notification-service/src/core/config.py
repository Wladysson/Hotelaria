from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Hotel Notification Service"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    JWT_SECRET_KEY: str = Field(
        default="change-me-in-production",
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    RABBITMQ_URL: str = Field(
        default="amqp://guest:guest@localhost:5672/",
    )

    RABBITMQ_EXCHANGE: str = "exchange.notifications"
    RABBITMQ_EXCHANGE_TYPE: str = "topic"

    RABBITMQ_NOTIFICATION_QUEUE: str = "notifications"
    RABBITMQ_NOTIFICATION_ROUTING_KEY: str = "notification.#"

    RABBITMQ_RESERVATION_QUEUE: str = "notification.reservations"
    RABBITMQ_RESERVATION_ROUTING_KEY: str = "reservation.#"

    RABBITMQ_PAYMENT_QUEUE: str = "notification.payments"
    RABBITMQ_PAYMENT_ROUTING_KEY: str = "payment.#"

    RABBITMQ_PREFETCH_COUNT: int = 10
    RABBITMQ_CONNECTION_TIMEOUT: int = 10
    RABBITMQ_RECONNECT_DELAY: int = 5
    RABBITMQ_MAX_RETRIES: int = 3

    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
    )

    REDIS_CACHE_TTL: int = 300

    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str | None = None
    SMTP_FROM_NAME: str = "Hotelaria"

    SMTP_USE_TLS: bool = True

    SEND_EMAIL_ENABLED: bool = True

    SMS_PROVIDER: str | None = None
    SMS_API_KEY: str | None = None
    SMS_API_URL: str | None = None

    SEND_SMS_ENABLED: bool = False

    PUSH_PROVIDER: str | None = None
    PUSH_API_KEY: str | None = None
    PUSH_API_URL: str | None = None

    SEND_PUSH_ENABLED: bool = False

    NOTIFICATION_MAX_RETRIES: int = 3
    NOTIFICATION_RETRY_DELAY: int = 5

    NOTIFICATION_BATCH_SIZE: int = 100

    CORS_ORIGINS: str = "http://localhost:5173"
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: str = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    CORS_ALLOW_HEADERS: str = "*"

    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]

    @property
    def cors_methods_list(self) -> list[str]:
        return [
            method.strip()
            for method in self.CORS_ALLOW_METHODS.split(",")
            if method.strip()
        ]

    @property
    def cors_headers_list(self) -> list[str]:
        if self.CORS_ALLOW_HEADERS.strip() == "*":
            return ["*"]

        return [
            header.strip()
            for header in self.CORS_ALLOW_HEADERS.split(",")
            if header.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()