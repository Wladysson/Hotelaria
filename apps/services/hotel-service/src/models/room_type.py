from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

if TYPE_CHECKING:
    from src.models.hotel import Hotel
    from src.models.room import Room


class RoomTypeStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class RoomType(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    """
    Representa uma categoria comercial de quarto.
    """

    __tablename__ = "room_types"

    __table_args__ = (
        Index(
            "ix_room_types_hotel_id",
            "hotel_id",
        ),
        Index(
            "ix_room_types_status",
            "status",
        ),
        Index(
            "ix_room_types_hotel_status",
            "hotel_id",
            "status",
        ),
        Index(
            "ix_room_types_slug",
            "slug",
        ),
    )

    #identificaçao
    hotel_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "hotels.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(180),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    #capacidade
    max_occupancy: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    max_adults: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    max_children: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    bed_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    #dimensoes
    area_square_meters: Mapped[Decimal | None] = mapped_column(
        Numeric(
            precision=8,
            scale=2,
        ),
        nullable=True,
    )

    #politics
    base_price: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=12,
            scale=2,
        ),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="BRL",
        server_default="BRL",
    )

    #status
    status: Mapped[RoomTypeStatus] = mapped_column(
        String(20),
        nullable=False,
        default=RoomTypeStatus.ACTIVE,
        server_default=RoomTypeStatus.ACTIVE.value,
    )

    is_available: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    #relacionamentos
    hotel: Mapped["Hotel"] = relationship(
        "Hotel",
        back_populates="room_types",
    )

    rooms: Mapped[list["Room"]] = relationship(
        "Room",
        back_populates="room_type",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )