from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class SearchHotelsRequest(BaseModel):
    city_id: UUID | None = None
    city_name: str | None = Field(default=None, min_length=2, max_length=150)
    check_in: date
    check_out: date
    guests: int = Field(default=1, ge=1, le=50)
    rooms: int = Field(default=1, ge=1, le=20)
    min_price: Decimal | None = Field(default=None, ge=0)
    max_price: Decimal | None = Field(default=None, ge=0)
    min_rating: int | None = Field(default=None, ge=1, le=5)
    star_rating: int | None = Field(default=None, ge=1, le=5)
    amenity_ids: list[UUID] = Field(default_factory=list)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @model_validator(mode="after")
    def validate_dates(self) -> "SearchHotelsRequest":
        if self.check_out <= self.check_in:
            raise ValueError("A data de checkout deve ser posterior ao check-in.")

        if (
            self.min_price is not None
            and self.max_price is not None
            and self.min_price > self.max_price
        ):
            raise ValueError(
                "O preço mínimo não pode ser maior que o preço máximo."
            )

        return self


class SearchHotelResponse(BaseModel):
    hotel_id: UUID
    hotel_name: str
    city_id: UUID
    city_name: str
    state: str
    address: str
    star_rating: int
    description: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    available_rooms: int
    lowest_price: Decimal | None = None
    image_url: str | None = None


class SearchHotelsResponse(BaseModel):
    items: list[SearchHotelResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AvailabilitySearchRequest(BaseModel):
    hotel_id: UUID | None = None
    city_id: UUID | None = None
    room_type_id: UUID | None = None
    check_in: date
    check_out: date
    guests: int = Field(default=1, ge=1, le=50)
    rooms: int = Field(default=1, ge=1, le=20)

    @model_validator(mode="after")
    def validate_dates(self) -> "AvailabilitySearchRequest":
        if self.check_out <= self.check_in:
            raise ValueError(
                "A data de checkout deve ser posterior ao check-in."
            )

        return self


class AvailabilityRoomResponse(BaseModel):
    room_id: UUID
    hotel_id: UUID
    hotel_name: str
    room_number: str
    room_type_id: UUID
    room_type_name: str
    capacity: int
    price_per_night: Decimal
    available: bool


class AvailabilityResponse(BaseModel):
    check_in: date
    check_out: date
    guests: int
    rooms: int
    items: list[AvailabilityRoomResponse]