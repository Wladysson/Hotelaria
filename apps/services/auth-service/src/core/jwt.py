from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

import jwt
from jwt.exceptions import InvalidTokenError

from src.core.config import settings


class JWTError(Exception):
    pass


class TokenType:
    ACCESS = "access"
    REFRESH = "refresh"
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"


def _create_token(
    *,
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    roles: list[str] | None = None,
    permissions: list[str] | None = None,
) -> tuple[str, str, datetime]:
    now = datetime.now(timezone.utc)
    expires_at = now + expires_delta
    jti = str(uuid4())

    payload: dict[str, Any] = {
        "sub": subject,
        "jti": jti,
        "type": token_type,
        "iat": now,
        "nbf": now,
        "exp": expires_at,
    }

    if roles is not None:
        payload["roles"] = roles

    if permissions is not None:
        payload["permissions"] = permissions

    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return token, jti, expires_at


def create_access_token(
    user_id: UUID,
    roles: list[str] | None = None,
    permissions: list[str] | None = None,
) -> tuple[str, str, datetime]:
    return _create_token(
        subject=str(user_id),
        token_type=TokenType.ACCESS,
        expires_delta=timedelta(
            minutes=settings.access_token_expire_minutes
        ),
        roles=roles,
        permissions=permissions,
    )


def create_refresh_token(
    user_id: UUID,
) -> tuple[str, str, datetime]:
    return _create_token(
        subject=str(user_id),
        token_type=TokenType.REFRESH,
        expires_delta=timedelta(
            days=settings.refresh_token_expire_days
        ),
    )


def create_password_reset_token(
    user_id: UUID,
) -> tuple[str, str, datetime]:
    return _create_token(
        subject=str(user_id),
        token_type=TokenType.PASSWORD_RESET,
        expires_delta=timedelta(
            minutes=settings.password_reset_token_expire_minutes
        ),
    )


def create_email_verification_token(
    user_id: UUID,
) -> tuple[str, str, datetime]:
    return _create_token(
        subject=str(user_id),
        token_type=TokenType.EMAIL_VERIFICATION,
        expires_delta=timedelta(
            minutes=settings.email_verification_token_expire_minutes
        ),
    )


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={
                "require": [
                    "sub",
                    "jti",
                    "type",
                    "iat",
                    "nbf",
                    "exp",
                ]
            },
        )
    except InvalidTokenError as exc:
        raise JWTError("Token inválido ou expirado.") from exc


def get_token_subject(token: str) -> UUID:
    payload = decode_token(token)

    try:
        return UUID(str(payload["sub"]))
    except (ValueError, TypeError, KeyError) as exc:
        raise JWTError("Subject do token inválido.") from exc


def get_token_jti(token: str) -> str:
    payload = decode_token(token)

    jti = payload.get("jti")

    if not jti:
        raise JWTError("JTI do token não encontrado.")

    return str(jti)


def get_token_type(token: str) -> str:
    payload = decode_token(token)

    token_type = payload.get("type")

    if not token_type:
        raise JWTError("Tipo do token não encontrado.")

    return str(token_type)


def get_token_roles(token: str) -> list[str]:
    payload = decode_token(token)

    roles = payload.get("roles", [])

    if not isinstance(roles, list):
        raise JWTError("Roles do token inválidas.")

    return [str(role) for role in roles]


def get_token_permissions(token: str) -> list[str]:
    payload = decode_token(token)

    permissions = payload.get("permissions", [])

    if not isinstance(permissions, list):
        raise JWTError("Permissions do token inválidas.")

    return [str(permission) for permission in permissions]