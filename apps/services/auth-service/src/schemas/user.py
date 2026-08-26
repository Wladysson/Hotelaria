from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_.-]+$",
    )
    first_name: str = Field(
        min_length=1,
        max_length=100,
    )
    last_name: str = Field(
        min_length=1,
        max_length=100,
    )


class UserCreate(UserBase):
    password: str = Field(
        min_length=8,
        max_length=128,
    )


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_.-]+$",
    )
    first_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    last_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    is_active: bool | None = None


class UserPasswordChange(BaseModel):
    current_password: str = Field(
        min_length=1,
        max_length=128,
    )

    new_password: str = Field(
        min_length=8,
        max_length=128,
    )

    confirm_password: str = Field(
        min_length=8,
        max_length=128,
    )


class UserPasswordResetRequest(BaseModel):
    email: EmailStr


class UserPasswordReset(BaseModel):
    token: str = Field(
        min_length=1,
    )

    new_password: str = Field(
        min_length=8,
        max_length=128,
    )

    confirm_password: str = Field(
        min_length=8,
        max_length=128,
    )


class UserEmailVerification(BaseModel):
    token: str = Field(
        min_length=1,
    )


class UserResponse(UserBase):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    is_active: bool
    is_verified: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None


class UserSummary(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    username: str
    email: EmailStr
    full_name: str
    is_active: bool
    is_verified: bool


class UserAdminUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_.-]+$",
    )
    first_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    last_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    is_active: bool | None = None
    is_verified: bool | None = None
    is_superuser: bool | None = None


class UserRoleAssignment(BaseModel):
    role_ids: list[UUID] = Field(
        min_length=1,
    )