from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class GuestCreate(BaseModel):
    first_name: str = Field(
        min_length=2,
        max_length=100,
    )

    last_name: str = Field(
        min_length=2,
        max_length=100,
    )

    document_number: str | None = Field(
        default=None,
        min_length=5,
        max_length=30,
    )

    email: EmailStr

    phone: str | None = Field(
        default=None,
        max_length=30,
    )

    address: str | None = Field(
        default=None,
        max_length=500,
    )

    city: str | None = Field(
        default=None,
        max_length=150,
    )

    state: str | None = Field(
        default=None,
        max_length=100,
    )

    country: str = Field(
        default="Brasil",
        min_length=2,
        max_length=100,
    )


class GuestUpdate(BaseModel):
    first_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    last_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    document_number: str | None = Field(
        default=None,
        min_length=5,
        max_length=30,
    )

    email: EmailStr | None = None

    phone: str | None = Field(
        default=None,
        max_length=30,
    )

    address: str | None = Field(
        default=None,
        max_length=500,
    )

    city: str | None = Field(
        default=None,
        max_length=150,
    )

    state: str | None = Field(
        default=None,
        max_length=100,
    )

    country: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )


class GuestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID | None
    first_name: str
    last_name: str
    document_number: str | None
    email: EmailStr
    phone: str | None
    address: str | None
    city: str | None
    state: str | None
    country: str
    is_primary: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class GuestSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: str
    email: EmailStr