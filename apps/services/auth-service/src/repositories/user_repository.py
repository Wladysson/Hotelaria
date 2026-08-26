from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User


class UserRepository:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)

        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )

        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email.lower())
        )

        return result.scalar_one_or_none()

    async def exists_by_email(self, email: str) -> bool:
        result = await self.session.execute(
            select(User.id)
            .where(User.email == email.lower())
            .limit(1)
        )

        return result.scalar_one_or_none() is not None

    async def update(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)

        return user

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
        await self.session.flush()