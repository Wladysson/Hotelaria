from uuid import uuid4

from src.core.jwt import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
)


def test_access_token_contains_user_subject():
    user_id = uuid4()

    token, jti, expires_at = create_access_token(
        user_id,
        roles=["user"],
        permissions=["users:read"],
    )

    payload = decode_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["type"] == TokenType.ACCESS
    assert payload["jti"] == jti
    assert expires_at is not None


def test_access_token_contains_roles():
    user_id = uuid4()

    token, _, _ = create_access_token(
        user_id,
        roles=["admin"],
        permissions=[
            "users:read",
            "users:update",
        ],
    )

    payload = decode_token(token)

    assert payload["roles"] == ["admin"]


def test_access_token_contains_permissions():
    user_id = uuid4()

    token, _, _ = create_access_token(
        user_id,
        roles=["admin"],
        permissions=[
            "users:read",
            "users:update",
        ],
    )

    payload = decode_token(token)

    assert "users:read" in payload["permissions"]
    assert "users:update" in payload["permissions"]


def test_refresh_token_has_refresh_type():
    user_id = uuid4()

    token, jti, expires_at = create_refresh_token(
        user_id
    )

    payload = decode_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["type"] == TokenType.REFRESH
    assert payload["jti"] == jti
    assert expires_at is not None