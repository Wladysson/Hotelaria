from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """Gera o hash bcrypt de uma senha."""
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Verifica uma senha em texto contra seu hash."""
    return pwd_context.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(
    subject: str,
    is_admin: bool,
    expires_delta: timedelta | None = None,
) -> str:
    """Cria um JWT de acesso para o usuário autenticado."""

    if expires_delta is None:
        expires_delta = timedelta(
            minutes=settings.access_token_expire_minutes
        )

    expire = datetime.now(timezone.utc) + expires_delta

    payload: dict[str, Any] = {
        "sub": subject,
        "is_admin": is_admin,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """Decodifica e valida um JWT."""

    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


def get_subject_from_token(token: str) -> str | None:
    """Obtém o identificador do usuário presente no JWT."""

    try:
        payload = decode_access_token(token)
    except JWTError:
        return None

    subject = payload.get("sub")

    if not isinstance(subject, str) or not subject:
        return None

    return subject