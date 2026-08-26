from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import hash_password
from src.models.user import User
from src.repositories.user_repository import UserRepository


class UserService:

    def __init__(self, session: AsyncSession):
        self.repository = UserRepository(session)

    async def create_user(
        self,
        email: str,
        password: str,
        role_id: UUID,
    ) -> User:
        existing_user = await self.repository.get_by_email(email)

        if existing_user is not None:
            raise ValueError("User with this email already exists")

        password_hash = hash_password(password)

        user = User(
            email=email,
            password_hash=password_hash,
            role_id=role_id,
            is_active=True,
        )

        return await self.repository.create(user)

    async def get_user_by_id(
        self,
        user_id: UUID,
    ) -> User | None:
        return await self.repository.get_by_id(user_id)

    async def deactivate_user(
        self,
        user_id: UUID,
    ) -> User | None:
        user = await self.repository.get_by_id(user_id)

        if user is None:
            return None

        user.is_active = False

        return await self.repository.update(user)