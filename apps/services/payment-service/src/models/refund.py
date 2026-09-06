from decimal import Decimal
from enum import Enum
from uuid import UUID

from sqlalchemy import Enum as SQLEnum, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class RefundStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RefundReason(str, Enum):
    CUSTOMER_REQUEST = "customer_request"
    CANCELLATION = "cancellation"
    DUPLICATE = "duplicate"
    FRAUD = "fraud"
    PAYMENT_ERROR = "payment_error"
    OTHER = "other"


class Refund(Base):
    __tablename__ = "refunds"

    transaction_id: Mapped[UUID] = mapped_column(
        nullable=False,
        index=True,
    )

    reservation_id: Mapped[UUID] = mapped_column(
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

    status: Mapped[RefundStatus] = mapped_column(
        SQLEnum(
            RefundStatus,
            name="refund_status",
            native_enum=True,
        ),
        nullable=False,
        default=RefundStatus.PENDING,
        index=True,
    )

    reason: Mapped[RefundReason] = mapped_column(
        SQLEnum(
            RefundReason,
            name="refund_reason",
            native_enum=True,
        ),
        nullable=False,
    )

    gateway_refund_id: Mapped[str | None] = mapped_column(
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

    failure_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    failure_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )