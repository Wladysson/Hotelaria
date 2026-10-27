import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.template import NotificationTemplate


class TemplateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        template: NotificationTemplate,
    ) -> NotificationTemplate:
        self.session.add(template)
        await self.session.flush()
        await self.session.refresh(template)

        return template

    async def get_by_id(
        self,
        template_id: uuid.UUID,
    ) -> NotificationTemplate | None:
        result = await self.session.execute(
            select(NotificationTemplate).where(
                NotificationTemplate.id == template_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_by_name(
        self,
        name: str,
    ) -> NotificationTemplate | None:
        result = await self.session.execute(
            select(NotificationTemplate).where(
                NotificationTemplate.name == name,
            )
        )

        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        notification_type: str | None = None,
        is_active: bool | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[NotificationTemplate]:
        query = select(NotificationTemplate)

        if notification_type is not None:
            query = query.where(
                NotificationTemplate.notification_type
                == notification_type
            )

        if is_active is not None:
            query = query.where(
                NotificationTemplate.is_active == is_active
            )

        query = (
            query
            .order_by(NotificationTemplate.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(query)

        return list(result.scalars().all())

    async def count(
        self,
        *,
        notification_type: str | None = None,
        is_active: bool | None = None,
    ) -> int:
        query = select(func.count(NotificationTemplate.id))

        if notification_type is not None:
            query = query.where(
                NotificationTemplate.notification_type
                == notification_type
            )

        if is_active is not None:
            query = query.where(
                NotificationTemplate.is_active == is_active
            )

        result = await self.session.execute(query)

        return result.scalar_one()

    async def update(
        self,
        template: NotificationTemplate,
    ) -> NotificationTemplate:
        await self.session.flush()
        await self.session.refresh(template)

        return template

    async def delete(
        self,
        template: NotificationTemplate,
    ) -> None:
        await self.session.delete(template)
        await self.session.flush()