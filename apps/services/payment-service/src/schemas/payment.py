from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.models.transaction import PaymentProvider


class PaymentCreate(BaseModel):
    reservation_id: UUID
    customer_id: UUID
    amount: Decimal = Field(
        gt=0,
        max_digits=18,
        decimal_places=2,
    )
    currency: str = Field(
        default="BRL",
        min_length=3,
        max_length=3,
    )
    payment_method_id: UUID
    provider: PaymentProvider
    description: str | None = Field(
        default=None,
        max_length=1000,
    )
    requires_capture: bool = False
    idempotency_key: str = Field(
        min_length=1,
        max_length=255,
    )
    metadata: dict[str, str] | None = None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()


class PaymentResponse(BaseModel):
    transaction_id: UUID
    reservation_id: UUID
    customer_id: UUID
    amount: Decimal
    currency: str
    provider: PaymentProvider
    status: str
    gateway_transaction_id: str | None = None
    requires_capture: bool
    captured_amount: Decimal
    message: str | None = None


class PaymentCaptureRequest(BaseModel):
    amount: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=18,
        decimal_places=2,
    )


class PaymentCancelRequest(BaseModel):
    reason: str | None = Field(
        default=None,
        max_length=500,
    )