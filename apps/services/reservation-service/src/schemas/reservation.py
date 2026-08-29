from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.schemas.guest import GuestResponse


class ReservationStatus(StrEnum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"


class ReservationItemCreate(BaseModel):
    room_id: UUID
    room_type_id: UUID
    check_in: date
    check_out: date
    guests: int = Field(default=1, ge=1, le=50)
    quantity: int = Field(default=1, ge=1, le=20)

    @model_validator(mode="after")
    def validate_dates(self) -> "ReservationItemCreate":
        if self.check_out <= self.check_in:
            raise ValueError(
                "A data de checkout deve ser posterior ao check-in."
            )

        return self


class ReservationCreate(BaseModel):
    hotel_id: UUID
    primary_guest_id: UUID | None = None
    guest: GuestResponse | None = None
    items: list[ReservationItemCreate] = Field(
        min_length=1,
        max_length=20,
    )
    special_requests: str | None = Field(
        default=None,
        max_length=2000,
    )
    idempotency_key: str = Field(
        min_length=8,
        max_length=255,
    )

    @model_validator(mode="after")
    def validate_guests(self) -> "ReservationCreate":
        if self.primary_guest_id is None and self.guest is None:
            raise ValueError(
                "Informe um hóspede principal ou os dados do hóspede."
            )

        return self


class ReservationItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    room_id: UUID
    room_type_id: UUID
    check_in: date
    check_out: date
    guests: int
    quantity: int
    price_per_night: Decimal
    total_amount: Decimal


class ReservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    reservation_code: str
    user_id: UUID | None
    hotel_id: UUID
    primary_guest_id: UUID | None
    status: ReservationStatus
    check_in: date
    check_out: date
    guests: int
    rooms: int
    subtotal: Decimal
    taxes: Decimal
    discounts: Decimal
    total_amount: Decimal
    special_requests: str | None
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime
    items: list[ReservationItemResponse]


class ReservationListResponse(BaseModel):
    items: list[ReservationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ReservationStatusResponse(BaseModel):
    reservation_id: UUID
    reservation_code: str
    status: ReservationStatus
    updated_at: datetime


class ReservationCancelRequest(BaseModel):
    reason: str = Field(
        min_length=3,
        max_length=1000,
    )


class ReservationCancelResponse(BaseModel):
    reservation_id: UUID
    reservation_code: str
    status: ReservationStatus
    refund_amount: Decimal
    cancellation_fee: Decimal
    cancelled_at: datetime