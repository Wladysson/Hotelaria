from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.permission import Permission
from src.models.role import Role


class RoleRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        role: Role,
    ) -> Role:
        self.session.add(role)

        await self.session.flush()
        await self.session.refresh(role)

        return role

    async def get_by_id(
        self,
        role_id: UUID,
    ) -> Role | None:
        statement = (
            select(Role)
            .where(Role.id == role_id)
            .options(
                selectinload(Role.permissions)
            )
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_by_name(
        self,
        name: str,
    ) -> Role | None:
        statement = (
            select(Role)
            .where(
                Role.name == name
            )
            .options(
                selectinload(Role.permissions)
            )
        )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def list_all(
        self,
        only_active: bool = True,
    ) -> list[Role]:
        statement = (
            select(Role)
            .options(
                selectinload(Role.permissions)
            )
            .order_by(Role.name)
        )

        if only_active:
            statement = statement.where(
                Role.is_active.is_(True)
            )

        result = await self.session.execute(statement)

        return list(result.scalars().unique().all())

    async def exists_by_name(
        self,
        name: str,
        exclude_role_id: UUID | None = None,
    ) -> bool:
        statement = (
            select(Role.id)
            .where(
                Role.name == name
            )
        )

        if exclude_role_id:
            statement = statement.where(
                Role.id != exclude_role_id
            )

        result = await self.session.execute(statement)

        return result.scalar_one_or_none() is not None

    async def get_permissions_by_ids(
        self,
        permission_ids: list[UUID],
    ) -> list[Permission]:
        if not permission_ids:
            return []

        statement = (
            select(Permission)
            .where(
                Permission.id.in_(permission_ids)
            )
            .where(
                Permission.is_active.is_(True)
            )
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all())

    async def get_all_permissions(self) -> list[Permission]:
        statement = (
            select(Permission)
            .where(
                Permission.is_active.is_(True)
            )
            .order_by(
                Permission.resource,
                Permission.action,
            )
        )

        result = await self.session.execute(statement)

        return list(result.scalars().all())

    async def add_permissions(
        self,
        role: Role,
        permissions: list[Permission],
    ) -> Role:
        role.permissions = permissions

        await self.session.flush()

        return role

    async def update(
        self,
        role: Role,
    ) -> Role:
        await self.session.flush()
        await self.session.refresh(role)

        return role

    async def delete(
        self,
        role: Role,
    ) -> None:
        await self.session.delete(role)

        await self.session.flush()