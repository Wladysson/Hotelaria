from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class HoldStatus(StrEnum):
    ACTIVE = "ACTIVE"
    CONFIRMED = "CONFIRMED"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class Hold(Base):
    __tablename__ = "holds"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    reservation_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "reservations.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    room_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    hotel_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    check_in: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    check_out: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    status: Mapped[HoldStatus] = mapped_column(
        String(20),
        nullable=False,
        default=HoldStatus.ACTIVE,
        index=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    idempotency_key: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
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

    reservation: Mapped["Reservation | None"] = relationship(
        "Reservation",
        back_populates="holds",
    )

    __table_args__ = (
        Index(
            "ix_holds_room_dates_status",
            "room_id",
            "check_in",
            "check_out",
            "status",
        ),
        Index(
            "ix_holds_expiration_status",
            "expires_at",
            "status",
        ),
    )