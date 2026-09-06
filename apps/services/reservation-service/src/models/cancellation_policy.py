from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class CancellationType(StrEnum):
    FREE = "FREE"
    PARTIAL = "PARTIAL"
    NON_REFUNDABLE = "NON_REFUNDABLE"


class CancellationPolicy(Base):
    __tablename__ = "cancellation_policies"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    cancellation_type: Mapped[CancellationType] = mapped_column(
        String(30),
        nullable=False,
        default=CancellationType.FREE,
    )

    free_cancellation_hours: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    refund_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("100.00"),
    )

    penalty_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    reservations: Mapped[list["Reservation"]] = relationship(
        "Reservation",
        back_populates="cancellation_policy",
    )