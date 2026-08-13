import pytest


async def cadastrar_usuario(client, email="usuario@test.com"):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "nome": "Usuário Teste",
            "email": email,
            "senha": "Senha@123",
        },
    )

    assert response.status_code == 201
    return response.json()


async def obter_token(client, email="usuario@test.com"):
    await cadastrar_usuario(client, email)

    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": "Senha@123",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_usuario_pode_consultar_proprio_perfil(client):
    token = await obter_token(client)

    response = await client.get(
        "/api/v1/usuarios/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "usuario@test.com"
    assert data["nome"] == "Usuário Teste"


@pytest.mark.asyncio
async def test_usuario_sem_token_nao_acessa_perfil(client):
    response = await client.get(
        "/api/v1/usuarios/me",
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_token_invalido_nao_acessa_perfil(client):
    response = await client.get(
        "/api/v1/usuarios/me",
        headers={
            "Authorization": "Bearer token-invalido",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_usuario_nao_acessa_outro_usuario(client):
    token = await obter_token(
        client,
        email="usuario1@test.com",
    )

    segundo_usuario = await cadastrar_usuario(
        client,
        email="usuario2@test.com",
    )

    response = await client.get(
        f"/api/v1/usuarios/{segundo_usuario['id']}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 403