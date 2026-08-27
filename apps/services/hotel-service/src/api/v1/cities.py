from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.deps import get_city_repository
from src.repositories.city_repository import CityRepository
from src.schemas.city import (
    CityCreate,
    CityResponse,
    CityUpdate,
)

router = APIRouter(
    prefix="/cities",
    tags=["Cities"],
)


@router.post(
    "/",
    response_model=CityResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_city(
    payload: CityCreate,
    repository: CityRepository = Depends(
        get_city_repository
    ),
):
    try:
        existing_city = await repository.get_by_name_and_state(
            name=payload.name,
            state=payload.state,
        )

        if existing_city is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe uma cidade com este nome e estado",
            )

        city = await repository.create_from_data(
            name=payload.name,
            state=payload.state,
            country=payload.country,
        )

        return city

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao criar cidade",
        )


@router.get(
    "/",
    response_model=list[CityResponse],
)
async def list_cities(
    active_only: bool = Query(
        default=True,
    ),
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
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
    repository: CityRepository = Depends(
        get_city_repository
    ),
):
    if search:
        return await repository.search(
            search=search.strip(),
            active_only=active_only,
            skip=skip,
            limit=limit,
        )

    return await repository.list(
        active_only=active_only,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{city_id}",
    response_model=CityResponse,
)
async def get_city(
    city_id: UUID,
    repository: CityRepository = Depends(
        get_city_repository
    ),
):
    city = await repository.get_by_id(city_id)

    if city is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cidade não encontrada",
        )

    return city


@router.put(
    "/{city_id}",
    response_model=CityResponse,
)
async def update_city(
    city_id: UUID,
    payload: CityUpdate,
    repository: CityRepository = Depends(
        get_city_repository
    ),
):
    city = await repository.get_by_id(city_id)

    if city is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cidade não encontrada",
        )

    if payload.name is not None:
        city.name = payload.name.strip()

    if payload.state is not None:
        city.state = payload.state.strip()

    if payload.country is not None:
        city.country = payload.country.strip()

    if (
        payload.name is not None
        or payload.state is not None
    ):
        existing_city = (
            await repository.get_by_name_and_state(
                name=city.name,
                state=city.state,
            )
        )

        if (
            existing_city is not None
            and existing_city.id != city.id
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe uma cidade com este nome e estado",
            )

    return await repository.update(city)


@router.patch(
    "/{city_id}/activate",
    response_model=CityResponse,
)
async def activate_city(
    city_id: UUID,
    repository: CityRepository = Depends(
        get_city_repository
    ),
):
    city = await repository.get_by_id(city_id)

    if city is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cidade não encontrada",
        )

    city.is_active = True

    return await repository.update(city)


@router.patch(
    "/{city_id}/deactivate",
    response_model=CityResponse,
)
async def deactivate_city(
    city_id: UUID,
    repository: CityRepository = Depends(
        get_city_repository
    ),
):
    city = await repository.get_by_id(city_id)

    if city is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cidade não encontrada",
        )

    city.is_active = False

    return await repository.update(city)


@router.delete(
    "/{city_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_city(
    city_id: UUID,
    repository: CityRepository = Depends(
        get_city_repository
    ),
):
    city = await repository.get_by_id(city_id)

    if city is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cidade não encontrada",
        )

    await repository.delete(city)

    return None