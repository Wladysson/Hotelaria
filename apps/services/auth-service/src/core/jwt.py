from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from src.core.config import settings


def create_access_token(
    subject: str,
    claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(timezone.utc)

    payload: dict[str, Any] = {
        "sub": subject,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(
            minutes=settings.access_token_expire_minutes
        ),
    }

    if claims:
        payload.update(claims)

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(
    subject: str,
    claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(timezone.utc)

    payload: dict[str, Any] = {
        "sub": subject,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(
            days=settings.refresh_token_expire_days
        ),
    }

    if claims:
        payload.update(claims)

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


def is_token_type(token: str, token_type: str) -> bool:
    payload = decode_token(token)
    return payload.get("type") == token_type