from decimal import Decimal
from enum import Enum
from uuid import UUID

from sqlalchemy import Enum as SQLEnum, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class PayoutStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PayoutProvider(str, Enum):
    STRIPE = "stripe"
    PAYPAL = "paypal"


class Payout(Base):
    __tablename__ = "payouts"

    merchant_id: Mapped[UUID] = mapped_column(
        nullable=False,
        index=True,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="BRL",
    )

    status: Mapped[PayoutStatus] = mapped_column(
        SQLEnum(
            PayoutStatus,
            name="payout_status",
            native_enum=True,
        ),
        nullable=False,
        default=PayoutStatus.PENDING,
        index=True,
    )

    provider: Mapped[PayoutProvider] = mapped_column(
        SQLEnum(
            PayoutProvider,
            name="payout_provider",
            native_enum=True,
        ),
        nullable=False,
    )

    gateway_payout_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
    )

    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    destination_account: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    failure_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    failure_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )