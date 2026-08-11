from decimal import Decimal
from enum import Enum
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Enum as SQLEnum,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class TransactionStatus(str, Enum):
    PENDING = "pending"
    AUTHORIZED = "authorized"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class TransactionType(str, Enum):
    PAYMENT = "payment"
    REFUND = "refund"
    PAYOUT = "payout"


class PaymentProvider(str, Enum):
    STRIPE = "stripe"
    PAYPAL = "paypal"


class Transaction(Base):
    __tablename__ = "transactions"

    reservation_id: Mapped[UUID] = mapped_column(
        ForeignKey("reservations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    customer_id: Mapped[UUID] = mapped_column(
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

    transaction_type: Mapped[TransactionType] = mapped_column(
        SQLEnum(
            TransactionType,
            name="transaction_type",
            native_enum=True,
        ),
        nullable=False,
        default=TransactionType.PAYMENT,
    )

    status: Mapped[TransactionStatus] = mapped_column(
        SQLEnum(
            TransactionStatus,
            name="transaction_status",
            native_enum=True,
        ),
        nullable=False,
        default=TransactionStatus.PENDING,
        index=True,
    )

    provider: Mapped[PaymentProvider | None] = mapped_column(
        SQLEnum(
            PaymentProvider,
            name="payment_provider",
            native_enum=True,
        ),
        nullable=True,
        index=True,
    )

    gateway_transaction_id: Mapped[str | None] = mapped_column(
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

    description: Mapped[str | None] = mapped_column(
        Text,
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

    requires_capture: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    captured_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    refunded_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    metadata_json: Mapped[dict | None] = mapped_column(
        nullable=True,
    )