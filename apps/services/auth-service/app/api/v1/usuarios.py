from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioResponse, UsuarioUpdate
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


@router.get(
    "/me",
    response_model=UsuarioResponse,
    summary="Retorna o usuário autenticado",
)
async def get_me(
    current_user: Usuario = Depends(get_current_user),
):
    return current_user


@router.get(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Busca um usuário por ID",
)
async def get_usuario(
    usuario_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UsuarioService(db)

    usuario = await service.get_by_id(usuario_id)

    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )

    # Usuário comum só pode consultar o próprio perfil.
    if not current_user.is_admin and current_user.id != usuario.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não possui permissão para acessar este usuário",
        )

    return usuario


@router.patch(
    "/me",
    response_model=UsuarioResponse,
    summary="Atualiza o perfil do usuário autenticado",
)
async def update_me(
    data: UsuarioUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UsuarioService(db)

    usuario = await service.update(
        usuario=current_user,
        data=data,
    )

    return usuario