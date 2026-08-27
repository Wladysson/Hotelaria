from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RoomTypeSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    capacity: int
    base_price: Decimal


class RoomBase(BaseModel):
    room_number: str = Field(..., min_length=1, max_length=30)
    floor: int = Field(default=0, ge=0)
    room_type_id: UUID
    price_per_night: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)
    is_active: bool = True


class RoomCreate(RoomBase):
    hotel_id: UUID


class RoomUpdate(BaseModel):
    room_number: str | None = Field(default=None, min_length=1, max_length=30)
    floor: int | None = Field(default=None, ge=0)
    room_type_id: UUID | None = None
    price_per_night: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=12,
        decimal_places=2,
    )
    is_active: bool | None = None


class RoomResponse(RoomBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    hotel_id: UUID
    created_at: datetime
    updated_at: datetime


class RoomDetailResponse(RoomResponse):
    room_type: RoomTypeSummary | None = None


class RoomListResponse(BaseModel):
    items: list[RoomResponse]
    total: int
    page: int
    page_size: int


class RoomAvailabilityResponse(BaseModel):
    room_id: UUID
    hotel_id: UUID
    room_number: str
    room_type_id: UUID
    available: bool
    price_per_night: Decimal
    check_in: datetime
    check_out: datetime