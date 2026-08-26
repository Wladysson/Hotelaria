from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import (
    create_password_hash,
    validate_password_strength,
)
from src.models.user import User
from src.repositories.role_repository import RoleRepository
from src.repositories.user_repository import UserRepository
from src.schemas.user import (
    UserAdminUpdate,
    UserCreate,
    UserRoleAssignment,
    UserUpdate,
)


class UserService:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session
        self.user_repository = UserRepository(session)
        self.role_repository = RoleRepository(session)

    async def create_user(
        self,
        data: UserCreate,
    ) -> User:
        email = str(data.email).lower().strip()
        username = data.username.strip()

        if await self.user_repository.exists_by_email(email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="E-mail já está cadastrado.",
            )

        if await self.user_repository.exists_by_username(username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Nome de usuário já está cadastrado.",
            )

        validate_password_strength(data.password)

        user = User(
            email=email,
            username=username,
            password_hash=create_password_hash(
                data.password
            ),
            first_name=data.first_name.strip(),
            last_name=data.last_name.strip(),
            is_active=True,
            is_verified=False,
            is_superuser=False,
        )

        return await self.user_repository.create(user)

    async def get_user(
        self,
        user_id: UUID,
    ) -> User:
        user = await self.user_repository.get_by_id_with_authorization(
            user_id
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado.",
            )

        return user

    async def get_user_by_email(
        self,
        email: str,
    ) -> User:
        user = await self.user_repository.get_by_email(
            email.strip().lower()
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado.",
            )

        return user

    async def update_user(
        self,
        user: User,
        data: UserUpdate,
    ) -> User:
        if data.email is not None:
            email = str(data.email).lower().strip()

            if await self.user_repository.exists_by_email(
                email,
                exclude_user_id=user.id,
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="E-mail já está cadastrado.",
                )

            user.email = email

        if data.username is not None:
            username = data.username.strip()

            if await self.user_repository.exists_by_username(
                username,
                exclude_user_id=user.id,
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Nome de usuário já está cadastrado.",
                )

            user.username = username

        if data.first_name is not None:
            user.first_name = data.first_name.strip()

        if data.last_name is not None:
            user.last_name = data.last_name.strip()

        if data.is_active is not None:
            user.is_active = data.is_active

        return await self.user_repository.update(user)

    async def admin_update_user(
        self,
        user: User,
        data: UserAdminUpdate,
    ) -> User:
        if data.email is not None:
            email = str(data.email).lower().strip()

            if await self.user_repository.exists_by_email(
                email,
                exclude_user_id=user.id,
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="E-mail já está cadastrado.",
                )

            user.email = email

        if data.username is not None:
            username = data.username.strip()

            if await self.user_repository.exists_by_username(
                username,
                exclude_user_id=user.id,
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Nome de usuário já está cadastrado.",
                )

            user.username = username

        if data.first_name is not None:
            user.first_name = data.first_name.strip()

        if data.last_name is not None:
            user.last_name = data.last_name.strip()

        if data.is_active is not None:
            user.is_active = data.is_active

        if data.is_verified is not None:
            user.is_verified = data.is_verified

        if data.is_superuser is not None:
            user.is_superuser = data.is_superuser

        return await self.user_repository.update(user)

    async def assign_roles(
        self,
        user: User,
        data: UserRoleAssignment,
    ) -> User:
        roles = []

        for role_id in data.role_ids:
            role = await self.role_repository.get_by_id(
                role_id
            )

            if role is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=(
                        f"Role {role_id} não encontrada."
                    ),
                )

            if not role.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Role {role.name} está inativa."
                    ),
                )

            roles.append(role)

        user.roles = roles

        await self.session.flush()

        return user

    async def remove_all_roles(
        self,
        user: User,
    ) -> User:
        user.roles = []

        await self.session.flush()

        return user

    async def verify_user(
        self,
        user: User,
    ) -> User:
        if user.is_verified:
            return user

        return await self.user_repository.mark_verified(
            user
        )

    async def deactivate_user(
        self,
        user: User,
    ) -> User:
        user.is_active = False

        return await self.user_repository.update(user)

    async def activate_user(
        self,
        user: User,
    ) -> User:
        user.is_active = True
        user.locked_until = None
        user.failed_login_attempts = 0

        return await self.user_repository.update(user)

    async def delete_user(
        self,
        user: User,
    ) -> None:
        await self.user_repository.delete(user)