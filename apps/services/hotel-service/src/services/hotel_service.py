from uuid import UUID

from src.models.hotel import Hotel
from src.repositories.hotel_repository import HotelRepository
from src.repositories.city_repository import CityRepository


class HotelService:

    def __init__(
        self,
        hotel_repository: HotelRepository,
        city_repository: CityRepository,
    ):
        self.hotel_repository = hotel_repository
        self.city_repository = city_repository

    async def create_hotel(
        self,
        name: str,
        description: str | None,
        address: str,
        city_id: UUID,
        star_rating: int,
        check_in_time: str,
        check_out_time: str,
    ) -> Hotel:
        city = await self.city_repository.get_by_id(city_id)

        if city is None:
            raise ValueError("Cidade não encontrada")

        existing_hotel = await self.hotel_repository.get_by_name_and_city(
            name=name,
            city_id=city_id,
        )

        if existing_hotel is not None:
            raise ValueError(
                "Já existe um hotel com este nome nesta cidade"
            )

        if star_rating < 1 or star_rating > 5:
            raise ValueError(
                "A classificação do hotel deve estar entre 1 e 5 estrelas"
            )

        hotel = Hotel(
            name=name.strip(),
            description=description,
            address=address.strip(),
            city_id=city_id,
            star_rating=star_rating,
            check_in_time=check_in_time,
            check_out_time=check_out_time,
            is_active=True,
        )

        return await self.hotel_repository.create(hotel)

    async def get_hotel(
        self,
        hotel_id: UUID,
    ) -> Hotel:
        hotel = await self.hotel_repository.get_by_id(hotel_id)

        if hotel is None:
            raise ValueError("Hotel não encontrado")

        return hotel

    async def get_hotel_with_details(
        self,
        hotel_id: UUID,
    ) -> Hotel:
        hotel = await self.hotel_repository.get_by_id_with_details(
            hotel_id
        )

        if hotel is None:
            raise ValueError("Hotel não encontrado")

        return hotel

    async def list_hotels(
        self,
        city_id: UUID | None = None,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Hotel]:
        if limit < 1:
            raise ValueError("O limite deve ser maior que zero")

        if limit > 100:
            limit = 100

        if skip < 0:
            skip = 0

        return await self.hotel_repository.list(
            city_id=city_id,
            active_only=active_only,
            skip=skip,
            limit=limit,
        )

    async def update_hotel(
        self,
        hotel_id: UUID,
        name: str | None = None,
        description: str | None = None,
        address: str | None = None,
        city_id: UUID | None = None,
        star_rating: int | None = None,
        check_in_time: str | None = None,
        check_out_time: str | None = None,
    ) -> Hotel:
        hotel = await self.hotel_repository.get_by_id(hotel_id)

        if hotel is None:
            raise ValueError("Hotel não encontrado")

        if city_id is not None:
            city = await self.city_repository.get_by_id(city_id)

            if city is None:
                raise ValueError("Cidade não encontrada")

            if city_id != hotel.city_id:
                existing_hotel = (
                    await self.hotel_repository.get_by_name_and_city(
                        name=name or hotel.name,
                        city_id=city_id,
                    )
                )

                if existing_hotel is not None:
                    raise ValueError(
                        "Já existe um hotel com este nome nesta cidade"
                    )

            hotel.city_id = city_id

        if name is not None:
            normalized_name = name.strip()

            if not normalized_name:
                raise ValueError(
                    "O nome do hotel não pode ser vazio"
                )

            if normalized_name.lower() != hotel.name.lower():
                existing_hotel = (
                    await self.hotel_repository.get_by_name_and_city(
                        name=normalized_name,
                        city_id=hotel.city_id,
                    )
                )

                if (
                    existing_hotel is not None
                    and existing_hotel.id != hotel.id
                ):
                    raise ValueError(
                        "Já existe um hotel com este nome nesta cidade"
                    )

            hotel.name = normalized_name

        if description is not None:
            hotel.description = description

        if address is not None:
            normalized_address = address.strip()

            if not normalized_address:
                raise ValueError(
                    "O endereço não pode ser vazio"
                )

            hotel.address = normalized_address

        if star_rating is not None:
            if star_rating < 1 or star_rating > 5:
                raise ValueError(
                    "A classificação do hotel deve estar entre 1 e 5 estrelas"
                )

            hotel.star_rating = star_rating

        if check_in_time is not None:
            hotel.check_in_time = check_in_time

        if check_out_time is not None:
            hotel.check_out_time = check_out_time

        return await self.hotel_repository.update(hotel)

    async def activate_hotel(
        self,
        hotel_id: UUID,
    ) -> Hotel:
        hotel = await self.hotel_repository.get_by_id(hotel_id)

        if hotel is None:
            raise ValueError("Hotel não encontrado")

        if hotel.is_active:
            return hotel

        hotel.is_active = True

        return await self.hotel_repository.update(hotel)

    async def deactivate_hotel(
        self,
        hotel_id: UUID,
    ) -> Hotel:
        hotel = await self.hotel_repository.get_by_id(hotel_id)

        if hotel is None:
            raise ValueError("Hotel não encontrado")

        if not hotel.is_active:
            return hotel

        hotel.is_active = False

        return await self.hotel_repository.update(hotel)

    async def delete_hotel(
        self,
        hotel_id: UUID,
    ) -> None:
        hotel = await self.hotel_repository.get_by_id(hotel_id)

        if hotel is None:
            raise ValueError("Hotel não encontrado")

        await self.hotel_repository.delete(hotel)