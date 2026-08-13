import pytest

from app.schemas.usuario import UsuarioCreate, UsuarioUpdate
from app.services.usuario_service import UsuarioService


@pytest.mark.asyncio
async def test_criar_usuario(db_session):
    service = UsuarioService(db_session)

    data = UsuarioCreate(
        nome="Wladyson",
        email="wladyson@test.com",
        senha="Senha@123",
    )

    usuario = await service.create(data)

    assert usuario.id is not None
    assert usuario.nome == "Wladyson"
    assert usuario.email == "wladyson@test.com"

    assert usuario.password_hash != "Senha@123"
    assert usuario.password_hash is not None


@pytest.mark.asyncio
async def test_buscar_usuario_por_id(db_session):
    service = UsuarioService(db_session)

    data = UsuarioCreate(
        nome="Wladyson",
        email="wladyson@test.com",
        senha="Senha@123",
    )

    usuario_criado = await service.create(data)

    usuario = await service.get_by_id(
        usuario_criado.id,
    )

    assert usuario is not None
    assert usuario.id == usuario_criado.id
    assert usuario.email == "wladyson@test.com"


@pytest.mark.asyncio
async def test_buscar_usuario_inexistente(db_session):
    service = UsuarioService(db_session)

    usuario = await service.get_by_id(999999)

    assert usuario is None


@pytest.mark.asyncio
async def test_atualizar_usuario(db_session):
    service = UsuarioService(db_session)

    data = UsuarioCreate(
        nome="Wladyson",
        email="wladyson@test.com",
        senha="Senha@123",
    )

    usuario = await service.create(data)

    update_data = UsuarioUpdate(
        nome="Wladyson Araújo",
    )

    usuario_atualizado = await service.update(
        usuario=usuario,
        data=update_data,
    )

    assert usuario_atualizado.nome == "Wladyson Araújo"
    assert usuario_atualizado.email == "wladyson@test.com"