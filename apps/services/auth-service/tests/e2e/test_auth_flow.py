import pytest


@pytest.mark.asyncio
async def test_authentication_endpoint_is_available(
    client,
):
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "test@example.com",
            "password": "InvalidPassword123!",
        },
    )

    assert response.status_code in {
        401,
        403,
    }