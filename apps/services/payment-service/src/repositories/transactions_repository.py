from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.transactions import Transaction, TransactionStatus


class TransactionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        transaction: Transaction,
    ) -> Transaction:
        self.session.add(transaction)
        await self.session.flush()
        await self.session.refresh(transaction)

        return transaction

    async def get_by_id(
        self,
        transaction_id: UUID,
    ) -> Transaction | None:
        result = await self.session.execute(
            select(Transaction).where(
                Transaction.id == transaction_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> Transaction | None:
        result = await self.session.execute(
            select(Transaction).where(
                Transaction.idempotency_key == idempotency_key,
            )
        )

        return result.scalar_one_or_none()

    async def get_by_gateway_transaction_id(
        self,
        gateway_transaction_id: str,
    ) -> Transaction | None:
        result = await self.session.execute(
            select(Transaction).where(
                Transaction.gateway_transaction_id
                == gateway_transaction_id,
            )
        )

        return result.scalar_one_or_none()

    async def list_by_customer(
        self,
        customer_id: UUID,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Transaction]:
        result = await self.session.execute(
            select(Transaction)
            .where(
                Transaction.customer_id == customer_id,
            )
            .order_by(Transaction.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        return list(result.scalars().all())

    async def list_by_reservation(
        self,
        reservation_id: UUID,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Transaction]:
        result = await self.session.execute(
            select(Transaction)
            .where(
                Transaction.reservation_id == reservation_id,
            )
            .order_by(Transaction.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        return list(result.scalars().all())

    async def list_by_status(
        self,
        status: TransactionStatus,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Transaction]:
        result = await self.session.execute(
            select(Transaction)
            .where(
                Transaction.status == status,
            )
            .order_by(Transaction.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        return list(result.scalars().all())

    async def count_by_customer(
        self,
        customer_id: UUID,
    ) -> int:
        result = await self.session.execute(
            select(func.count(Transaction.id)).where(
                Transaction.customer_id == customer_id,
            )
        )

        return result.scalar_one()

    async def count_by_reservation(
        self,
        reservation_id: UUID,
    ) -> int:
        result = await self.session.execute(
            select(func.count(Transaction.id)).where(
                Transaction.reservation_id == reservation_id,
            )
        )

        return result.scalar_one()

    async def update(
        self,
        transaction: Transaction,
        **values,
    ) -> Transaction:
        for field, value in values.items():
            if hasattr(transaction, field):
                setattr(transaction, field, value)

        await self.session.flush()
        await self.session.refresh(transaction)

        return transaction

    async def delete(
        self,
        transaction: Transaction,
    ) -> None:
        await self.session.delete(transaction)
        await self.session.flush()