from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
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
    from src.models.room_type import RoomType


class RoomStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    OUT_OF_SERVICE = "out_of_service"


class Room(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    """
    Representa uma unidade física de hospedagem.
    """

    __tablename__ = "rooms"

    __table_args__ = (
        Index(
            "ix_rooms_hotel_id",
            "hotel_id",
        ),
        Index(
            "ix_rooms_room_type_id",
            "room_type_id",
        ),
        Index(
            "ix_rooms_status",
            "status",
        ),
        Index(
            "ix_rooms_hotel_status",
            "hotel_id",
            "status",
        ),
        Index(
            "ix_rooms_room_type_status",
            "room_type_id",
            "status",
        ),
    )
#relacionamentos princiapis
    hotel_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "hotels.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    room_type_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "room_types.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

#identificaçao fisica
    number: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    floor: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

#caracteristicas
    has_accessibility: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    smoking_allowed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

#operaçao
    status: Mapped[RoomStatus] = mapped_column(
        String(30),
        nullable=False,
        default=RoomStatus.ACTIVE,
        server_default=RoomStatus.ACTIVE.value,
    )

    is_bookable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

#relacionamento

    hotel: Mapped["Hotel"] = relationship(
        "Hotel",
        back_populates="rooms",
    )

    room_type: Mapped["RoomType"] = relationship(
        "RoomType",
        back_populates="rooms",
    )