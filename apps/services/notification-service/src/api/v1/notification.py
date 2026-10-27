import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_session
from src.models.notification import NotificationStatus, NotificationType
from src.schemas.notifications import (
    NotificationCreate,
    NotificationResponse,
    NotificationUpdate,
)
from src.services.notification_service import NotificationService


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


def get_notification_service(
    session: AsyncSession = Depends(get_session),
) -> NotificationService:
    return NotificationService(session)


@router.post(
    "",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma nova notificação",
)
async def create_notification(
    data: NotificationCreate,
    service: NotificationService = Depends(get_notification_service),
) -> NotificationResponse:
    return await service.create(data)


@router.get(
    "",
    response_model=list[NotificationResponse],
    summary="Lista notificações",
)
async def list_notifications(
    status_filter: NotificationStatus | None = Query(
        default=None,
        alias="status",
    ),
    notification_type: NotificationType | None = None,
    recipient: str | None = Query(default=None, min_length=1),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    service: NotificationService = Depends(get_notification_service),
) -> list[NotificationResponse]:
    return await service.list(
        status=status_filter,
        notification_type=notification_type,
        recipient=recipient,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
    summary="Busca uma notificação",
)
async def get_notification(
    notification_id: uuid.UUID,
    service: NotificationService = Depends(get_notification_service),
) -> NotificationResponse:
    try:
        return await service.get_by_id(notification_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{notification_id}",
    response_model=NotificationResponse,
    summary="Atualiza uma notificação",
)
async def update_notification(
    notification_id: uuid.UUID,
    data: NotificationUpdate,
    service: NotificationService = Depends(get_notification_service),
) -> NotificationResponse:
    try:
        return await service.update(notification_id, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/{notification_id}/cancel",
    response_model=NotificationResponse,
    summary="Cancela uma notificação",
)
async def cancel_notification(
    notification_id: uuid.UUID,
    service: NotificationService = Depends(get_notification_service),
) -> NotificationResponse:
    try:
        return await service.cancel(notification_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc