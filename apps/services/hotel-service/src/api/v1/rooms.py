from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.deps import get_current_user
from src.schemas.room import (
    RoomCreate,
    RoomResponse,
    RoomUpdate,
)
from src.services.room_service import RoomService
from src.core.dependencies import get_room_service


router = APIRouter(
    prefix="/rooms",
    tags=["Rooms"],
)


@router.post(
    "/",
    response_model=RoomResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um quarto",
)
async def create_room(
    data: RoomCreate,
    service: RoomService = Depends(get_room_service),
    current_user=Depends(get_current_user),
):
    return await service.create_room(
        data=data,
        current_user=current_user,
    )


@router.get(
    "/{room_id}",
    response_model=RoomResponse,
    summary="Obtém um quarto",
)
async def get_room(
    room_id: UUID,
    service: RoomService = Depends(get_room_service),
):
    room = await service.get_room(room_id)

    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quarto não encontrado.",
        )

    return room


@router.put(
    "/{room_id}",
    response_model=RoomResponse,
    summary="Atualiza um quarto",
)
async def update_room(
    room_id: UUID,
    data: RoomUpdate,
    service: RoomService = Depends(get_room_service),
    current_user=Depends(get_current_user),
):
    room = await service.update_room(
        room_id=room_id,
        data=data,
        current_user=current_user,
    )

    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quarto não encontrado.",
        )

    return room


@router.delete(
    "/{room_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove um quarto",
)
async def delete_room(
    room_id: UUID,
    service: RoomService = Depends(get_room_service),
    current_user=Depends(get_current_user),
):
    deleted = await service.delete_room(
        room_id=room_id,
        current_user=current_user,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quarto não encontrado.",
        )


@router.get(
    "/hotel/{hotel_id}",
    response_model=list[RoomResponse],
    summary="Lista os quartos de um hotel",
)
async def list_hotel_rooms(
    hotel_id: UUID,
    active_only: bool = Query(
        default=True,
        description="Retorna somente quartos ativos.",
    ),
    service: RoomService = Depends(get_room_service),
):
    return await service.list_hotel_rooms(
        hotel_id=hotel_id,
        active_only=active_only,
    )


@router.patch(
    "/{room_id}/activate",
    response_model=RoomResponse,
    summary="Ativa um quarto",
)
async def activate_room(
    room_id: UUID,
    service: RoomService = Depends(get_room_service),
    current_user=Depends(get_current_user),
):
    room = await service.activate_room(
        room_id=room_id,
        current_user=current_user,
    )

    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quarto não encontrado.",
        )

    return room


@router.patch(
    "/{room_id}/deactivate",
    response_model=RoomResponse,
    summary="Desativa um quarto",
)
async def deactivate_room(
    room_id: UUID,
    service: RoomService = Depends(get_room_service),
    current_user=Depends(get_current_user),
):
    room = await service.deactivate_room(
        room_id=room_id,
        current_user=current_user,
    )

    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quarto não encontrado.",
        )

    return room