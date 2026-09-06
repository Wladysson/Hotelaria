from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class ReservationItem(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    """
    Representa um quarto incluído em uma reserva.
    """

    __tablename__ = "reservation_items"

    reservation_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "reservations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    room_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    room_type_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    room_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    room_type_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    nights: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    guests_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    price_per_night: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=12,
            scale=2,
        ),
        nullable=False,
    )

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=12,
            scale=2,
        ),
        nullable=False,
    )

    reservation = relationship(
        "Reservation",
        back_populates="items",
    )