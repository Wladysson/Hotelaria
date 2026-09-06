from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.models.refund import RefundReason, RefundStatus


class RefundCreate(BaseModel):
    transaction_id: UUID
    reservation_id: UUID
    amount: Decimal = Field(
        gt=0,
        max_digits=18,
        decimal_places=2,
    )
    reason: RefundReason
    idempotency_key: str = Field(
        min_length=1,
        max_length=255,
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
    )


class RefundResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    transaction_id: UUID
    reservation_id: UUID
    amount: Decimal
    currency: str
    status: RefundStatus
    reason: RefundReason
    gateway_refund_id: str | None
    idempotency_key: str
    failure_code: str | None
    failure_message: str | None
    created_at: datetime
    updated_at: datetime


class RefundStatusResponse(BaseModel):
    id: UUID
    transaction_id: UUID
    status: RefundStatus
    amount: Decimal
    gateway_refund_id: str | None
    failure_code: str | None
    failure_message: str | None


class RefundListResponse(BaseModel):
    items: list[RefundResponse]
    total: int
    page: int
    size: int
    pages: int