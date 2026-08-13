import pytest

@pytest.mark.asyncio
async def test_cadastro_usuario(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "nome": "Wladyson",
            "email": "wladyson@test.com",
            "senha": "Senha@123",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "wladyson@test.com"
    assert data["nome"] == "Wladyson"
    assert "senha" not in data
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_login_usuario(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "nome": "Wladyson",
            "email": "wladyson@test.com",
            "senha": "Senha@123",
        },
    )

    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "wladyson@test.com",
            "password": "Senha@123",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_senha_incorreta(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "nome": "Wladyson",
            "email": "wladyson@test.com",
            "senha": "Senha@123",
        },
    )

    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "wladyson@test.com",
            "password": "senha-errada",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_cadastro_email_duplicado(client):
    payload = {
        "nome": "Wladyson",
        "email": "wladyson@test.com",
        "senha": "Senha@123",
    }

    first_response = await client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = await client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    assert second_response.status_code == 409