from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

from src.core.config import settings


password_hash = PasswordHash.recommended()


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_prefix}/auth/login",
    auto_error=True,
)


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return password_hash.verify(
        plain_password,
        hashed_password,
    )


def validate_password_length(password: str) -> None:
    password_length = len(password)

    if password_length < settings.password_min_length:
        raise ValueError(
            f"A senha deve possuir no mínimo "
            f"{settings.password_min_length} caracteres."
        )

    if password_length > settings.password_max_length:
        raise ValueError(
            f"A senha deve possuir no máximo "
            f"{settings.password_max_length} caracteres."
        )


def validate_password_strength(password: str) -> None:
    validate_password_length(password)

    if password.islower():
        raise ValueError(
            "A senha deve possuir pelo menos uma letra maiúscula."
        )

    if password.isupper():
        raise ValueError(
            "A senha deve possuir pelo menos uma letra minúscula."
        )

    if not any(character.isdigit() for character in password):
        raise ValueError(
            "A senha deve possuir pelo menos um número."
        )

    if not any(
        not character.isalnum()
        for character in password
    ):
        raise ValueError(
            "A senha deve possuir pelo menos um caractere especial."
        )


def create_password_hash(password: str) -> str:
    validate_password_strength(password)
    return hash_password(password)


def check_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return verify_password(
        plain_password,
        hashed_password,
    )