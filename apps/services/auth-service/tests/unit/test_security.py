from src.core.security import (
    check_password,
    create_password_hash,
    validate_password_strength,
)


def test_password_hash_is_not_plaintext():
    password = "StrongPassword123!"

    password_hash = create_password_hash(
        password
    )

    assert password_hash != password


def test_password_hash_can_be_verified():
    password = "StrongPassword123!"

    password_hash = create_password_hash(
        password
    )

    assert check_password(
        password,
        password_hash,
    )


def test_invalid_password_is_rejected():
    password = "StrongPassword123!"

    password_hash = create_password_hash(
        password
    )

    assert not check_password(
        "WrongPassword123!",
        password_hash,
    )


def test_password_strength_accepts_valid_password():
    validate_password_strength(
        "StrongPassword123!"
    )


def test_password_strength_rejects_weak_password():
    try:
        validate_password_strength(
            "123"
        )
    except ValueError:
        return

    raise AssertionError(
        "Senha fraca deveria ser rejeitada."
    )