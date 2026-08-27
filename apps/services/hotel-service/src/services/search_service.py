from datetime import date
from uuid import UUID

from src.repositories.search_repository import SearchRepository


class SearchService:

    def __init__(
        self,
        search_repository: SearchRepository,
    ):
        self.search_repository = search_repository

    async def search_hotels(
        self,
        city_id: UUID | None = None,
        city_name: str | None = None,
        check_in: date | None = None,
        check_out: date | None = None,
        guests: int = 1,
        min_price: float | None = None,
        max_price: float | None = None,
        min_rating: int | None = None,
        amenities: list[UUID] | None = None,
        skip: int = 0,
        limit: int = 20,
    ):
        self._validate_dates(
            check_in=check_in,
            check_out=check_out,
        )

        self._validate_guests(guests)

        self._validate_price(
            min_price=min_price,
            max_price=max_price,
        )

        self._validate_rating(min_rating)

        if skip < 0:
            skip = 0

        if limit < 1:
            limit = 1

        if limit > 100:
            limit = 100

        normalized_city_name = (
            city_name.strip()
            if city_name
            else None
        )

        return await self.search_repository.search_hotels(
            city_id=city_id,
            city_name=normalized_city_name,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            min_price=min_price,
            max_price=max_price,
            min_rating=min_rating,
            amenities=amenities,
            skip=skip,
            limit=limit,
        )

    async def search_by_city(
        self,
        city_id: UUID,
        check_in: date | None = None,
        check_out: date | None = None,
        guests: int = 1,
        skip: int = 0,
        limit: int = 20,
    ):
        return await self.search_hotels(
            city_id=city_id,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            skip=skip,
            limit=limit,
        )

    async def search_by_location(
        self,
        city_name: str,
        check_in: date | None = None,
        check_out: date | None = None,
        guests: int = 1,
        skip: int = 0,
        limit: int = 20,
    ):
        if not city_name.strip():
            raise ValueError(
                "A cidade deve ser informada"
            )

        return await self.search_hotels(
            city_name=city_name,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    def _validate_dates(
        check_in: date | None,
        check_out: date | None,
    ) -> None:
        if check_in is None and check_out is None:
            return

        if check_in is None or check_out is None:
            raise ValueError(
                "As datas de check-in e check-out devem ser informadas"
            )

        if check_in < date.today():
            raise ValueError(
                "A data de check-in não pode estar no passado"
            )

        if check_out <= check_in:
            raise ValueError(
                "A data de check-out deve ser posterior ao check-in"
            )

    @staticmethod
    def _validate_guests(
        guests: int,
    ) -> None:
        if guests < 1:
            raise ValueError(
                "A quantidade de hóspedes deve ser maior que zero"
            )

        if guests > 50:
            raise ValueError(
                "A quantidade máxima de hóspedes por busca é 50"
            )

    @staticmethod
    def _validate_price(
        min_price: float | None,
        max_price: float | None,
    ) -> None:
        if min_price is not None and min_price < 0:
            raise ValueError(
                "O preço mínimo não pode ser negativo"
            )

        if max_price is not None and max_price < 0:
            raise ValueError(
                "O preço máximo não pode ser negativo"
            )

        if (
            min_price is not None
            and max_price is not None
            and min_price > max_price
        ):
            raise ValueError(
                "O preço mínimo não pode ser maior que o preço máximo"
            )

    @staticmethod
    def _validate_rating(
        min_rating: int | None,
    ) -> None:
        if min_rating is None:
            return

        if min_rating < 1 or min_rating > 5:
            raise ValueError(
                "A classificação mínima deve estar entre 1 e 5"
            )