from enum import Enum
from uuid import UUID

from sqlalchemy import Boolean, Enum as SQLEnum, String
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class PaymentMethodType(str, Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PIX = "pix"
    BANK_TRANSFER = "bank_transfer"
    WALLET = "wallet"


class PaymentMethodStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    customer_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    method_type: Mapped[PaymentMethodType] = mapped_column(
        SQLEnum(
            PaymentMethodType,
            name="payment_method_type",
            native_enum=True,
        ),
        nullable=False,
    )

    status: Mapped[PaymentMethodStatus] = mapped_column(
        SQLEnum(
            PaymentMethodStatus,
            name="payment_method_status",
            native_enum=True,
        ),
        nullable=False,
        default=PaymentMethodStatus.ACTIVE,
        index=True,
    )

    provider: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    provider_method_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    card_brand: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    card_last_four: Mapped[str | None] = mapped_column(
        String(4),
        nullable=True,
    )

    card_expiry_month: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    card_expiry_year: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )