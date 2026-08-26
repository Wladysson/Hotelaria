from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.role import Role


class RoleRepository:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, role: Role) -> Role:
        self.session.add(role)
        await self.session.flush()
        await self.session.refresh(role)

        return role

    async def get_by_id(self, role_id: UUID) -> Role | None:
        result = await self.session.execute(
            select(Role)
            .options(selectinload(Role.users))
            .where(Role.id == role_id)
        )

        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Role | None:
        result = await self.session.execute(
            select(Role)
            .where(Role.name == name)
        )

        return result.scalar_one_or_none()

    async def list_all(self) -> list[Role]:
        result = await self.session.execute(
            select(Role).order_by(Role.name)
        )

        return list(result.scalars().all())

    async def exists_by_name(self, name: str) -> bool:
        result = await self.session.execute(
            select(Role.id)
            .where(Role.name == name)
            .limit(1)
        )

        return result.scalar_one_or_none() is not None