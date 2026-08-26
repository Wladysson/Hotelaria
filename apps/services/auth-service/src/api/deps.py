from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.jwt import JWTError
from src.core.security import oauth2_scheme
from src.models.user import User
from src.repositories.user_repository import UserRepository
from src.services.auth_service import AuthService
from src.services.token_service import TokenService
from src.services.user_service import UserService


DBSession = Annotated[
    AsyncSession,
    Depends(get_db),
]


async def get_current_user(
    token: Annotated[
        str,
        Depends(oauth2_scheme),
    ],
    db: DBSession,
) -> User:
    token_service = TokenService()

    try:
        user_id = token_service.validate_access_token(
            token
        )
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
    User,
    Depends(get_current_user),
]


def get_auth_service(
    db: DBSession,
) -> AuthService:
    return AuthService(db)


AuthServiceDependency = Annotated[
    AuthService,
    Depends(get_auth_service),
]


def get_user_service(
    db: DBSession,
) -> UserService:
    return UserService(db)


UserServiceDependency = Annotated[
    UserService,
    Depends(get_user_service),
]


def get_token_service() -> TokenService:
    return TokenService()


TokenServiceDependency = Annotated[
    TokenService,
    Depends(get_token_service),
]


def require_roles(
    *required_roles: str,
):
    async def dependency(
        current_user: CurrentUser,
    ) -> User:
        user_roles = {
            role.name
            for role in current_user.roles
            if role.is_active
        }

        if not set(required_roles).issubset(
            user_roles
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Usuário não possui "
                    "as roles necessárias."
                ),
            )

        return current_user

    return dependency


def require_permissions(
    *required_permissions: str,
):
    async def dependency(
        current_user: CurrentUser,
    ) -> User:
        user_permissions = {
            permission.name
            for role in current_user.roles
            if role.is_active
            for permission in role.permissions
            if permission.is_active
        }

        if not set(required_permissions).issubset(
            user_permissions
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Usuário não possui "
                    "as permissões necessárias."
                ),
            )

        return current_user

    return dependency


def require_superuser(
    current_user: CurrentUser,
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Acesso restrito a administradores."
            ),
        )

    return current_user