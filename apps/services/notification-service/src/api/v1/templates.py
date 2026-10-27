import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_session
from src.schemas.template import (
    TemplateCreate,
    TemplateResponse,
    TemplateUpdate,
)
from src.services.template_service import TemplateService


router = APIRouter(
    prefix="/templates",
    tags=["Templates"],
)


def get_template_service(
    session: AsyncSession = Depends(get_session),
) -> TemplateService:
    return TemplateService(session)


@router.post(
    "",
    response_model=TemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um template de notificação",
)
async def create_template(
    data: TemplateCreate,
    service: TemplateService = Depends(get_template_service),
) -> TemplateResponse:
    try:
        return await service.create(data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=list[TemplateResponse],
    summary="Lista templates de notificação",
)
async def list_templates(
    notification_type: str | None = Query(
        default=None,
        min_length=1,
        max_length=20,
    ),
    is_active: bool | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    service: TemplateService = Depends(get_template_service),
) -> list[TemplateResponse]:
    return await service.list(
        notification_type=notification_type,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/by-name/{name}",
    response_model=TemplateResponse,
    summary="Busca template pelo nome",
)
async def get_template_by_name(
    name: str,
    service: TemplateService = Depends(get_template_service),
) -> TemplateResponse:
    try:
        return await service.get_by_name(name)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/{template_id}",
    response_model=TemplateResponse,
    summary="Busca template pelo identificador",
)
async def get_template(
    template_id: uuid.UUID,
    service: TemplateService = Depends(get_template_service),
) -> TemplateResponse:
    try:
        return await service.get_by_id(template_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{template_id}",
    response_model=TemplateResponse,
    summary="Atualiza um template",
)
async def update_template(
    template_id: uuid.UUID,
    data: TemplateUpdate,
    service: TemplateService = Depends(get_template_service),
) -> TemplateResponse:
    try:
        return await service.update(template_id, data)
    except ValueError as exc:
        if "nome" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/{template_id}/activate",
    response_model=TemplateResponse,
    summary="Ativa um template",
)
async def activate_template(
    template_id: uuid.UUID,
    service: TemplateService = Depends(get_template_service),
) -> TemplateResponse:
    try:
        return await service.activate(template_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/{template_id}/deactivate",
    response_model=TemplateResponse,
    summary="Desativa um template",
)
async def deactivate_template(
    template_id: uuid.UUID,
    service: TemplateService = Depends(get_template_service),
) -> TemplateResponse:
    try:
        return await service.deactivate(template_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove um template",
)
async def delete_template(
    template_id: uuid.UUID,
    service: TemplateService = Depends(get_template_service),
) -> None:
    try:
        await service.delete(template_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc