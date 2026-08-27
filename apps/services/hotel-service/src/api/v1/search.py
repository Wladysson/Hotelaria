from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from src.schemas.search import (
    HotelSearchResponse,
    HotelSearchRequest,
)
from src.services.search_services import SearchService
from src.core.dependencies import get_search_service


router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


@router.get(
    "/hotels",
    response_model=HotelSearchResponse,
    summary="Pesquisa hotéis",
)
async def search_hotels(
    city_id: UUID | None = Query(
        default=None,
        description="Identificador da cidade.",
    ),
    city: str | None = Query(
        default=None,
        description="Nome da cidade.",
    ),
    check_in: date | None = Query(
        default=None,
        description="Data de entrada.",
    ),
    check_out: date | None = Query(
        default=None,
        description="Data de saída.",
    ),
    guests: int = Query(
        default=1,
        ge=1,
        description="Quantidade de hóspedes.",
    ),
    rooms: int = Query(
        default=1,
        ge=1,
        description="Quantidade de quartos.",
    ),
    min_price: float | None = Query(
        default=None,
        ge=0,
        description="Preço mínimo.",
    ),
    max_price: float | None = Query(
        default=None,
        ge=0,
        description="Preço máximo.",
    ),
    stars: int | None = Query(
        default=None,
        ge=1,
        le=5,
        description="Classificação mínima do hotel.",
    ),
    service: SearchService = Depends(get_search_service),
):
    request = HotelSearchRequest(
        city_id=city_id,
        city=city,
        check_in=check_in,
        check_out=check_out,
        guests=guests,
        rooms=rooms,
        min_price=min_price,
        max_price=max_price,
        stars=stars,
    )

    return await service.search_hotels(request)


@router.get(
    "/hotels/{hotel_id}",
    summary="Pesquisa disponibilidade de um hotel",
)
async def search_hotel(
    hotel_id: UUID,
    check_in: date | None = Query(
        default=None,
        description="Data de entrada.",
    ),
    check_out: date | None = Query(
        default=None,
        description="Data de saída.",
    ),
    guests: int = Query(
        default=1,
        ge=1,
        description="Quantidade de hóspedes.",
    ),
    rooms: int = Query(
        default=1,
        ge=1,
        description="Quantidade de quartos.",
    ),
    service: SearchService = Depends(get_search_service),
):
    return await service.search_hotel(
        hotel_id=hotel_id,
        check_in=check_in,
        check_out=check_out,
        guests=guests,
        rooms=rooms,
    )