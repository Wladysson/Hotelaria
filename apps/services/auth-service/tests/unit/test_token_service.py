from uuid import uuid4

from src.models.user import User
from src.services.token_service import TokenService


def test_token_service_creates_access_token():
    user = User(
        id=uuid4(),
        email="user@example.com",
        username="user",
        password_hash="hashed-password",
        first_name="Test",
        last_name="User",
        is_active=True,
        is_verified=True,
        is_superuser=False,
    )

    token_service = TokenService()

    token, jti, expires_at = (
        token_service.create_access_token(user)
    )

    assert token
    assert jti
    assert expires_at


def test_token_service_creates_refresh_token():
    user = User(
        id=uuid4(),
        email="user@example.com",
        username="user",
        password_hash="hashed-password",
        first_name="Test",
        last_name="User",
        is_active=True,
        is_verified=True,
        is_superuser=False,
    )

    token_service = TokenService()

    token, jti, expires_at = (
        token_service.create_refresh_token(user)
    )

    assert token
    assert jti
    assert expires_at