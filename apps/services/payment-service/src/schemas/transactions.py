from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.models.transactions import (
    PaymentProvider,
    TransactionStatus,
    TransactionType,
)


class TransactionCreate(BaseModel):
    reservation_id: UUID
    customer_id: UUID
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    currency: str = Field(default="BRL", min_length=3, max_length=3)
    transaction_type: TransactionType = TransactionType.PAYMENT
    provider: PaymentProvider | None = None
    payment_method_id: UUID | None = None
    idempotency_key: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    requires_capture: bool = False
    metadata: dict[str, str] | None = None


class TransactionUpdate(BaseModel):
    status: TransactionStatus | None = None
    gateway_transaction_id: str | None = Field(
        default=None,
        max_length=255,
    )
    failure_code: str | None = Field(
        default=None,
        max_length=100,
    )
    failure_message: str | None = None
    captured_amount: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=18,
        decimal_places=2,
    )
    refunded_amount: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=18,
        decimal_places=2,
    )


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reservation_id: UUID
    customer_id: UUID
    amount: Decimal
    currency: str
    transaction_type: TransactionType
    status: TransactionStatus
    provider: PaymentProvider | None
    gateway_transaction_id: str | None
    idempotency_key: str
    description: str | None
    failure_code: str | None
    failure_message: str | None
    requires_capture: bool
    captured_amount: Decimal
    refunded_amount: Decimal
    metadata: dict[str, str] | None = None
    created_at: datetime
    updated_at: datetime


class TransactionListResponse(BaseModel):
    items: list[TransactionResponse]
    total: int
    page: int
    size: int
    pages: int