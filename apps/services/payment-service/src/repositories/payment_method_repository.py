from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.payment_method import (
    PaymentMethod,
    PaymentMethodStatus,
    PaymentMethodType,
)


class PaymentMethodRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        payment_method: PaymentMethod,
    ) -> PaymentMethod:
        self.session.add(payment_method)
        await self.session.flush()
        await self.session.refresh(payment_method)

        return payment_method

    async def get_by_id(
        self,
        payment_method_id: UUID,
    ) -> PaymentMethod | None:
        result = await self.session.execute(
            select(PaymentMethod).where(
                PaymentMethod.id == payment_method_id,
            )
        )

        return result.scalar_one_or_none()

    async def list_by_customer(
        self,
        customer_id: UUID,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[PaymentMethod]:
        result = await self.session.execute(
            select(PaymentMethod)
            .where(
                PaymentMethod.customer_id == customer_id,
            )
            .order_by(PaymentMethod.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        return list(result.scalars().all())

    async def list_active_by_customer(
        self,
        customer_id: UUID,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[PaymentMethod]:
        result = await self.session.execute(
            select(PaymentMethod)
            .where(
                PaymentMethod.customer_id == customer_id,
                PaymentMethod.status == PaymentMethodStatus.ACTIVE,
            )
            .order_by(PaymentMethod.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        return list(result.scalars().all())

    async def get_default_by_customer(
        self,
        customer_id: UUID,
    ) -> PaymentMethod | None:
        result = await self.session.execute(
            select(PaymentMethod).where(
                PaymentMethod.customer_id == customer_id,
                PaymentMethod.is_default.is_(True),
                PaymentMethod.status == PaymentMethodStatus.ACTIVE,
            )
        )

        return result.scalar_one_or_none()

    async def get_by_provider_method_id(
        self,
        provider_method_id: str,
    ) -> PaymentMethod | None:
        result = await self.session.execute(
            select(PaymentMethod).where(
                PaymentMethod.provider_method_id
                == provider_method_id,
            )
        )

        return result.scalar_one_or_none()

    async def list_by_type(
        self,
        customer_id: UUID,
        method_type: PaymentMethodType,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[PaymentMethod]:
        result = await self.session.execute(
            select(PaymentMethod)
            .where(
                PaymentMethod.customer_id == customer_id,
                PaymentMethod.method_type == method_type,
            )
            .order_by(PaymentMethod.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        return list(result.scalars().all())

    async def update(
        self,
        payment_method: PaymentMethod,
        **values,
    ) -> PaymentMethod:
        for field, value in values.items():
            if hasattr(payment_method, field):
                setattr(payment_method, field, value)

        await self.session.flush()
        await self.session.refresh(payment_method)

        return payment_method

    async def deactivate(
        self,
        payment_method: PaymentMethod,
    ) -> PaymentMethod:
        payment_method.status = PaymentMethodStatus.INACTIVE

        await self.session.flush()
        await self.session.refresh(payment_method)

        return payment_method

    async def delete(
        self,
        payment_method: PaymentMethod,
    ) -> None:
        await self.session.delete(payment_method)
        await self.session.flush()