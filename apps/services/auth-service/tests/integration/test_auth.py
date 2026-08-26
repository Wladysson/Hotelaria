import pytest


@pytest.mark.asyncio
async def test_login_with_invalid_credentials(
    client,
):
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "unknown",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401