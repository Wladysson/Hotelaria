from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class HoldStatus(StrEnum):
    ACTIVE = "ACTIVE"
    CONFIRMED = "CONFIRMED"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class AvailabilityRequest(BaseModel):
    hotel_id: UUID
    check_in: date
    check_out: date
    guests: int = Field(
        default=1,
        ge=1,
        le=50,
    )
    rooms: int = Field(
        default=1,
        ge=1,
        le=20,
    )
    room_type_id: UUID | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> "AvailabilityRequest":
        if self.check_out <= self.check_in:
            raise ValueError(
                "A data de checkout deve ser posterior ao check-in."
            )

        return self


class AvailableRoomResponse(BaseModel):
    room_id: UUID
    hotel_id: UUID
    room_type_id: UUID
    room_type_name: str
    room_number: str
    capacity: int
    price_per_night: Decimal
    available: bool


class AvailabilityResponse(BaseModel):
    hotel_id: UUID
    check_in: date
    check_out: date
    guests: int
    rooms: int
    available: bool
    items: list[AvailableRoomResponse]


class HoldCreateRequest(BaseModel):
    reservation_id: UUID | None = None
    hotel_id: UUID
    room_id: UUID
    check_in: date
    check_out: date
    duration_seconds: int = Field(
        default=600,
        ge=30,
        le=3600,
    )
    idempotency_key: str = Field(
        min_length=8,
        max_length=255,
    )

    @model_validator(mode="after")
    def validate_dates(self) -> "HoldCreateRequest":
        if self.check_out <= self.check_in:
            raise ValueError(
                "A data de checkout deve ser posterior ao check-in."
            )

        return self


class HoldResponse(BaseModel):
    id: UUID
    reservation_id: UUID | None
    room_id: UUID
    hotel_id: UUID
    check_in: date
    check_out: date
    status: HoldStatus
    expires_at: datetime
    created_at: datetime
    updated_at: datetime


class HoldReleaseResponse(BaseModel):
    hold_id: UUID
    status: HoldStatus
    released_at: datetime