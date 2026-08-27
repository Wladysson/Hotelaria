from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.deps import get_hotel_service
from src.schemas.hotel import (
    HotelCreate,
    HotelResponse,
    HotelUpdate,
)
from src.services.hotel_service import HotelService

router = APIRouter(
    prefix="/hotels",
    tags=["Hotels"],
)


@router.post(
    "/",
    response_model=HotelResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_hotel(
    payload: HotelCreate,
    service: HotelService = Depends(
        get_hotel_service
    ),
):
    try:
        return await service.create_hotel(
            name=payload.name,
            description=payload.description,
            address=payload.address,
            city_id=payload.city_id,
            star_rating=payload.star_rating,
            check_in_time=payload.check_in_time,
            check_out_time=payload.check_out_time,
        )

    except ValueError as exc:
        detail = str(exc)

        if "não encontrada" in detail.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail,
            )

        if "já existe" in detail.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=detail,
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


@router.get(
    "/",
    response_model=list[HotelResponse],
)
async def list_hotels(
    city_id: UUID | None = Query(
        default=None,
    ),
    active_only: bool = Query(
        default=True,
    ),
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    service: HotelService = Depends(
        get_hotel_service
    ),
):
    return await service.list_hotels(
        city_id=city_id,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{hotel_id}",
    response_model=HotelResponse,
)
async def get_hotel(
    hotel_id: UUID,
    service: HotelService = Depends(
        get_hotel_service
    ),
):
    try:
        return await service.get_hotel(
            hotel_id
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.get(
    "/{hotel_id}/details",
    response_model=HotelResponse,
)
async def get_hotel_details(
    hotel_id: UUID,
    service: HotelService = Depends(
        get_hotel_service
    ),
):
    try:
        return await service.get_hotel_with_details(
            hotel_id
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.put(
    "/{hotel_id}",
    response_model=HotelResponse,
)
async def update_hotel(
    hotel_id: UUID,
    payload: HotelUpdate,
    service: HotelService = Depends(
        get_hotel_service
    ),
):
    try:
        return await service.update_hotel(
            hotel_id=hotel_id,
            name=payload.name,
            description=payload.description,
            address=payload.address,
            city_id=payload.city_id,
            star_rating=payload.star_rating,
            check_in_time=payload.check_in_time,
            check_out_time=payload.check_out_time,
        )

    except ValueError as exc:
        detail = str(exc)

        if "não encontrado" in detail.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=detail,
            )

        if "já existe" in detail.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=detail,
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


@router.patch(
    "/{hotel_id}/activate",
    response_model=HotelResponse,
)
async def activate_hotel(
    hotel_id: UUID,
    service: HotelService = Depends(
        get_hotel_service
    ),
):
    try:
        return await service.activate_hotel(
            hotel_id
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.patch(
    "/{hotel_id}/deactivate",
    response_model=HotelResponse,
)
async def deactivate_hotel(
    hotel_id: UUID,
    service: HotelService = Depends(
        get_hotel_service
    ),
):
    try:
        return await service.deactivate_hotel(
            hotel_id
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.delete(
    "/{hotel_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_hotel(
    hotel_id: UUID,
    service: HotelService = Depends(
        get_hotel_service
    ),
):
    try:
        await service.delete_hotel(
            hotel_id
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    return None