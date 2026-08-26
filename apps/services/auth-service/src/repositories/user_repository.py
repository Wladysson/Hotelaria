from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.user import User


class UserRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user: User) -> User:
        self.session.add(user)

        await self.session.flush()
        await self.session.refresh(user)

        return user

    async def get_by_id(
        self,
        user_id: UUID,
    ) -> User | None:
        statement = (
            select(User)
            .where(User.id == user_id)
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_by_id_with_authorization(
        self,
        user_id: UUID,
    ) -> User | None:
        statement = (
            select(User)
            .options(
                selectinload(User.roles)
                .selectinload("permissions")
            )
            .where(User.id == user_id)
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_by_email(
        self,
        email: str,
    ) -> User | None:
        statement = (
            select(User)
            .where(
                User.email == email.lower()
            )
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_by_username(
        self,
        username: str,
    ) -> User | None:
        statement = (
            select(User)
            .where(
                User.username == username
            )
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_by_login(
        self,
        login: str,
    ) -> User | None:
        normalized_login = login.strip().lower()

        statement = (
            select(User)
            .where(
                or_(
                    User.email == normalized_login,
                    User.username == normalized_login,
                )
            )
            .options(
                selectinload(User.roles)
                .selectinload("permissions")
            )
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def exists_by_email(
        self,
        email: str,
        exclude_user_id: UUID | None = None,
    ) -> bool:
        statement = (
            select(User.id)
            .where(
                User.email == email.lower()
            )
        )

        if exclude_user_id:
            statement = statement.where(
                User.id != exclude_user_id
            )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none() is not None

    async def exists_by_username(
        self,
        username: str,
        exclude_user_id: UUID | None = None,
    ) -> bool:
        statement = (
            select(User.id)
            .where(
                User.username == username
            )
        )

        if exclude_user_id:
            statement = statement.where(
                User.id != exclude_user_id
            )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none() is not None

    async def update(
        self,
        user: User,
    ) -> User:
        await self.session.flush()
        await self.session.refresh(user)

        return user

    async def delete(
        self,
        user: User,
    ) -> None:
        await self.session.delete(user)
        await self.session.flush()

    async def increment_failed_login(
        self,
        user: User,
    ) -> User:
        user.failed_login_attempts += 1

        await self.session.flush()

        return user

    async def reset_failed_login(
        self,
        user: User,
    ) -> User:
        user.failed_login_attempts = 0
        user.locked_until = None

        await self.session.flush()

        return user

    async def lock_user(
        self,
        user: User,
        locked_until: datetime,
    ) -> User:
        user.locked_until = locked_until

        await self.session.flush()

        return user

    async def update_last_login(
        self,
        user: User,
    ) -> User:
        user.last_login_at = datetime.now(timezone.utc)
        user.failed_login_attempts = 0
        user.locked_until = None

        await self.session.flush()

        return user

    async def mark_verified(
        self,
        user: User,
    ) -> User:
        user.is_verified = True

        await self.session.flush()

        return user

    async def update_password(
        self,
        user: User,
        password_hash: str,
    ) -> User:
        user.password_hash = password_hash
        user.password_changed_at = datetime.now(
            timezone.utc
        )

        await self.session.flush()

        return user