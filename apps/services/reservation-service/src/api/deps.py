from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_session

from src.repositories.guest_repository import GuestRepository
from src.repositories.hold_repository import HoldRepository
from src.repositories.reservation_repository import ReservationRepository

from src.services.availability_service import AvailabilityService
from src.services.inventory_service import InventoryService
from src.services.pricing_service import PricingService
from src.services.reservation_service import ReservationService

from src.services.saga.booking_saga import BookingSaga
from src.services.saga.cancellation_saga import CancellationSaga
from src.services.saga.saga_orchestrator import SagaOrchestrator


async def get_session() -> AsyncGenerator[AsyncSession, None]:

    async for session in get_db_session():
        yield session


def get_reservation_repository(
    session: AsyncSession = Depends(get_session),
) -> ReservationRepository:
    return ReservationRepository(session)


def get_guest_repository(
    session: AsyncSession = Depends(get_session),
) -> GuestRepository:
    return GuestRepository(session)


def get_hold_repository(
    session: AsyncSession = Depends(get_session),
) -> HoldRepository:
    return HoldRepository(session)


def get_availability_service(
    repository: ReservationRepository = Depends(
        get_reservation_repository
    ),
) -> AvailabilityService:
    return AvailabilityService(
        reservation_repository=repository,
    )


def get_inventory_service(
    repository: ReservationRepository = Depends(
        get_reservation_repository
    ),
) -> InventoryService:
    return InventoryService(
        reservation_repository=repository,
    )


def get_pricing_service() -> PricingService:
    return PricingService()


def get_booking_saga(
    availability_service: AvailabilityService = Depends(
        get_availability_service
    ),
    inventory_service: InventoryService = Depends(
        get_inventory_service
    ),
    pricing_service: PricingService = Depends(
        get_pricing_service
    ),
) -> BookingSaga:
    return BookingSaga(
        availability_service=availability_service,
        inventory_service=inventory_service,
        pricing_service=pricing_service,
    )


def get_cancellation_saga(
    reservation_repository: ReservationRepository = Depends(
        get_reservation_repository
    ),
    inventory_service: InventoryService = Depends(
        get_inventory_service
    ),
) -> CancellationSaga:
    return CancellationSaga(
        reservation_repository=reservation_repository,
        inventory_service=inventory_service,
    )


def get_saga_orchestrator(
    booking_saga: BookingSaga = Depends(get_booking_saga),
    cancellation_saga: CancellationSaga = Depends(
        get_cancellation_saga
    ),
) -> SagaOrchestrator:
    return SagaOrchestrator(
        booking_saga=booking_saga,
        cancellation_saga=cancellation_saga,
    )


def get_reservation_service(
    reservation_repository: ReservationRepository = Depends(
        get_reservation_repository
    ),
    guest_repository: GuestRepository = Depends(
        get_guest_repository
    ),
    hold_repository: HoldRepository = Depends(
        get_hold_repository
    ),
    availability_service: AvailabilityService = Depends(
        get_availability_service
    ),
    inventory_service: InventoryService = Depends(
        get_inventory_service
    ),
) -> ReservationService:
    return ReservationService(
        reservation_repository=reservation_repository,
        guest_repository=guest_repository,
        hold_repository=hold_repository,
        availability_service=availability_service,
        inventory_service=inventory_service,
    )