from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Index,
    String,
    Table,
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


hotel_amenities = Table(
    "hotel_amenities",
    Base.metadata,
    Column(
        "hotel_id",
        PG_UUID(as_uuid=True),
        ForeignKey(
            "hotels.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
    Column(
        "amenity_id",
        PG_UUID(as_uuid=True),
        ForeignKey(
            "amenities.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
    Index(
        "ix_hotel_amenities_hotel_id",
        "hotel_id",
    ),
    Index(
        "ix_hotel_amenities_amenity_id",
        "amenity_id",
    ),
)


class AmenityType(str, Enum):
    HOTEL = "hotel"
    ROOM = "room"
    BOTH = "both"


class Amenity(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    """
    Representa uma comodidade disponível no catálogo.
    """

    __tablename__ = "amenities"

    __table_args__ = (
        Index(
            "ix_amenities_name",
            "name",
        ),
        Index(
            "ix_amenities_slug",
            "slug",
            unique=True,
        ),
        Index(
            "ix_amenities_type",
            "type",
        ),
        Index(
            "ix_amenities_active",
            "is_active",
        ),
    )

    #identificaçao

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        unique=True,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    icon: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )


    # classificaçao

    type: Mapped[AmenityType] = mapped_column(
        String(20),
        nullable=False,
        default=AmenityType.HOTEL,
        server_default=AmenityType.HOTEL.value,
    )

   #status

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    # relacionamento

    hotels: Mapped[list["Hotel"]] = relationship(
        "Hotel",
        secondary=hotel_amenities,
        back_populates="amenities",
        lazy="selectin",
    )