from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CityBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    state: str = Field(..., min_length=2, max_length=100)
    country: str = Field(default="Brasil", min_length=2, max_length=100)


class CityCreate(CityBase):
    pass


class CityUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    state: str | None = Field(default=None, min_length=2, max_length=100)
    country: str | None = Field(default=None, min_length=2, max_length=100)


class CityResponse(CityBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class CityListResponse(BaseModel):
    items: list[CityResponse]
    total: int
    page: int
    page_size: int