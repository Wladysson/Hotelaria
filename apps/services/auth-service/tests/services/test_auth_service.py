import pytest

from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)


def test_password_hash_nao_e_igual_a_senha():
    senha = "Senha@123"

    password_hash = get_password_hash(senha)

    assert password_hash != senha


def test_password_hash_pode_ser_validado():
    senha = "Senha@123"

    password_hash = get_password_hash(senha)

    assert verify_password(senha, password_hash) is True


def test_password_incorreta_falha():
    senha = "Senha@123"

    password_hash = get_password_hash(senha)

    assert verify_password(
        "senha-errada",
        password_hash,
    ) is False


def test_password_hash_e_diferente_a_cada_geracao():
    senha = "Senha@123"

    hash_1 = get_password_hash(senha)
    hash_2 = get_password_hash(senha)

    assert hash_1 != hash_2

    assert verify_password(senha, hash_1)
    assert verify_password(senha, hash_2)


def test_create_access_token():
    token = create_access_token(
        data={
            "sub": "1",
            "email": "usuario@test.com",
        }
    )

    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0