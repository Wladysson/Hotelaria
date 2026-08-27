from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.jwt import (
    JWTError,
    TokenType,
    decode_token,
    get_token_subject,
    get_token_type,
)
from src.core.security import oauth2_scheme
from src.repositories.user_repository import UserRepository


DBSession = Annotated[
    AsyncSession,
    Depends(get_db),
]


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DBSession,
):
    try:
        payload = decode_token(token)

        if payload.get("type") != TokenType.ACCESS:
            raise JWTError("Token de acesso obrigatório.")

        user_id = get_token_subject(token)

    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={
                "WWW-Authenticate": "Bearer",
            },
        ) from exc

    repository = UserRepository(db)

    user = await repository.get_by_id_with_authorization(
        user_id
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo.",
        )

    return user


CurrentUser = Annotated[
    object,
    Depends(get_current_user),
]


def require_roles(*required_roles: str):
    async def dependency(
        current_user: CurrentUser,
    ):
        user_roles = {
            role.name
            for role in current_user.roles
        }

        if not set(required_roles).issubset(user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário não possui as roles necessárias.",
            )

        return current_user

    return dependency


def require_permissions(*required_permissions: str):
    async def dependency(
        current_user: CurrentUser,
    ):
        user_permissions = {
            permission.name
            for role in current_user.roles
            for permission in role.permissions
        }

        if not set(required_permissions).issubset(
            user_permissions
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário não possui as permissões necessárias.",
            )

        return current_user

    return dependency


def require_superuser(current_user: CurrentUser):
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores.",
        )

    return current_user