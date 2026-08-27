from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(
        min_length=1,
    )


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


class TokenPayload(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
    )

    sub: UUID
    jti: str
    type: str
    iat: datetime
    nbf: datetime
    exp: datetime
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)


class AuthenticationResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int


class SessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None
    is_revoked: bool


class ActiveSessionsResponse(BaseModel):
    sessions: list[SessionResponse]
    total: int