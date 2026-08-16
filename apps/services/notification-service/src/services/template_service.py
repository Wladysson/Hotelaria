import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.template import NotificationTemplate
from src.repositories.template_repository import TemplateRepository
from src.schemas.template import TemplateCreate, TemplateUpdate


class TemplateService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = TemplateRepository(session)

    async def create(
        self,
        data: TemplateCreate,
    ) -> NotificationTemplate:
        existing_template = await self.repository.get_by_name(
            data.name,
        )

        if existing_template is not None:
            raise ValueError(
                "Já existe um template com este nome",
            )

        template = NotificationTemplate(
            name=data.name,
            description=data.description,
            subject_template=data.subject_template,
            content_template=data.content_template,
            notification_type=data.notification_type,
            is_active=data.is_active,
        )

        return await self.repository.create(template)

    async def get_by_id(
        self,
        template_id: uuid.UUID,
    ) -> NotificationTemplate:
        template = await self.repository.get_by_id(template_id)

        if template is None:
            raise ValueError("Template não encontrado")

        return template

    async def get_by_name(
        self,
        name: str,
    ) -> NotificationTemplate:
        template = await self.repository.get_by_name(name)

        if template is None:
            raise ValueError("Template não encontrado")

        return template

    async def list(
        self,
        *,
        notification_type: str | None = None,
        is_active: bool | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[NotificationTemplate]:
        return await self.repository.list(
            notification_type=notification_type,
            is_active=is_active,
            skip=skip,
            limit=limit,
        )

    async def update(
        self,
        template_id: uuid.UUID,
        data: TemplateUpdate,
    ) -> NotificationTemplate:
        template = await self.get_by_id(template_id)

        updates = data.model_dump(exclude_unset=True)

        if "name" in updates:
            existing_template = await self.repository.get_by_name(
                updates["name"],
            )

            if (
                existing_template is not None
                and existing_template.id != template.id
            ):
                raise ValueError(
                    "Já existe um template com este nome",
                )

        for field, value in updates.items():
            setattr(template, field, value)

        return await self.repository.update(template)

    async def activate(
        self,
        template_id: uuid.UUID,
    ) -> NotificationTemplate:
        template = await self.get_by_id(template_id)

        template.is_active = True

        return await self.repository.update(template)

    async def deactivate(
        self,
        template_id: uuid.UUID,
    ) -> NotificationTemplate:
        template = await self.get_by_id(template_id)

        template.is_active = False

        return await self.repository.update(template)

    async def delete(
        self,
        template_id: uuid.UUID,
    ) -> None:
        template = await self.get_by_id(template_id)

        await self.repository.delete(template)