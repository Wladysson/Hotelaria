from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_session
from src.services.gateway.gateway_factory import GatewayFactory
from src.services.payment_service import PaymentService
from src.services.refund_service import RefundService


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db_session():
        yield session


def get_gateway_factory() -> GatewayFactory:
    return GatewayFactory()


def get_payment_service(
    session: AsyncSession = Depends(get_session),
    gateway_factory: GatewayFactory = Depends(get_gateway_factory),
) -> PaymentService:
    return PaymentService(
        session=session,
        gateway_factory=gateway_factory,
    )


def get_refund_service(
    session: AsyncSession = Depends(get_session),
    gateway_factory: GatewayFactory = Depends(get_gateway_factory),
) -> RefundService:
    return RefundService(
        session=session,
        gateway_factory=gateway_factory,
    )