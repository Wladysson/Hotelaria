from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_current_user_id, get_db
from src.repositories.user_repository import UserRepository
from src.models.user import User


async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
) -> User:
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identity",
        )

    repository = UserRepository(session)

    user = await repository.get_by_id(user_uuid)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


def require_role(required_role: str):
    async def role_dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:
        user_roles = {role.name for role in current_user.roles}

        if required_role not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return role_dependency