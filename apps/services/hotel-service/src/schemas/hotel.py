from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class HotelBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    address: str = Field(..., min_length=3, max_length=300)
    postal_code: str | None = Field(default=None, max_length=20)
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)
    star_rating: int = Field(default=1, ge=1, le=5)
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=255)
    website: str | None = Field(default=None, max_length=500)
    check_in_time: str = Field(default="14:00", pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    check_out_time: str = Field(default="12:00", pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")


class HotelCreate(HotelBase):
    city_id: UUID


class HotelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    address: str | None = Field(default=None, min_length=3, max_length=300)
    postal_code: str | None = Field(default=None, max_length=20)
    city_id: UUID | None = None
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)
    star_rating: int | None = Field(default=None, ge=1, le=5)
    phone: str | None = Field(default=None, max_length=30)
    email: str | None = Field(default=None, max_length=255)
    website: str | None = Field(default=None, max_length=500)
    check_in_time: str | None = Field(
        default=None,
        pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$",
    )
    check_out_time: str | None = Field(
        default=None,
        pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$",
    )
    is_active: bool | None = None


class HotelResponse(HotelBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    city_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class HotelDetailResponse(HotelResponse):
    city: object | None = None
    rooms: list[object] = Field(default_factory=list)
    amenities: list[object] = Field(default_factory=list)
    images: list[object] = Field(default_factory=list)


class HotelListResponse(BaseModel):
    items: list[HotelResponse]
    total: int
    page: int
    page_size: int