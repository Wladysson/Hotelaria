from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from src.services.availability_service import AvailabilityService
from src.services.inventory_service import InventoryService
from src.services.pricing_service import PricingService


@dataclass
class BookingSagaResult:
    success: bool
    hotel_id: UUID
    rooms: int
    total_amount: Decimal
    inventory_reserved: bool


class BookingSaga:
    """
    Orquestra o processo distribuído de criação de uma reserva.

    Fluxo:

    1. valida disponibilidade;
    2. calcula o preço;
    3. reserva o inventário;
    4. retorna o estado da operação.

    Em caso de falha, a operação deve ser compensada pelo
    orchestrator responsável pela Saga.
    """

    def __init__(
        self,
        availability_service: AvailabilityService,
        inventory_service: InventoryService,
        pricing_service: PricingService,
    ) -> None:
        self.availability_service = availability_service
        self.inventory_service = inventory_service
        self.pricing_service = pricing_service

    async def execute(
        self,
        hotel_id: UUID,
        check_in,
        check_out,
        guests: int,
        rooms: int,
        price_per_night: Decimal,
        discount_percent: Decimal = Decimal("0"),
        tax_percent: Decimal = Decimal("0"),
    ) -> BookingSagaResult:

        available = await self.availability_service.check_availability(
            hotel_id=hotel_id,
            check_in=check_in,
            check_out=check_out,
            guests=guests,
            rooms=rooms,
        )

        if not available:
            return BookingSagaResult(
                success=False,
                hotel_id=hotel_id,
                rooms=rooms,
                total_amount=Decimal("0"),
                inventory_reserved=False,
            )

        total_amount = self.pricing_service.calculate_total(
            price_per_night=price_per_night,
            check_in=check_in,
            check_out=check_out,
            rooms=rooms,
            discount_percent=discount_percent,
            tax_percent=tax_percent,
        )

        inventory_reserved = (
            await self.inventory_service.reserve_inventory(
                hotel_id=hotel_id,
                check_in=check_in,
                check_out=check_out,
                rooms=rooms,
            )
        )

        if not inventory_reserved:
            return BookingSagaResult(
                success=False,
                hotel_id=hotel_id,
                rooms=rooms,
                total_amount=total_amount,
                inventory_reserved=False,
            )

        return BookingSagaResult(
            success=True,
            hotel_id=hotel_id,
            rooms=rooms,
            total_amount=total_amount,
            inventory_reserved=True,
        )