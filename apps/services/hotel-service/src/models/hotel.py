import uuid
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

if TYPE_CHECKING:
    from src.models.amenity import Amenity
    from src.models.city import City
    from src.models.image import Image
    from src.models.room import Room
    from src.models.room_type import RoomType


class HotelStatus(str, Enum):
    """
    Estados possíveis de um hotel no catálogo.
    """

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class Hotel(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    """
    Representa um hotel no catálogo da plataforma.
    """

    __tablename__ = "hotels"

    __table_args__ = (
        Index(
            "ix_hotels_city_id",
            "city_id",
        ),
        Index(
            "ix_hotels_slug",
            "slug",
            unique=True,
        ),
        Index(
            "ix_hotels_status",
            "status",
        ),
        Index(
            "ix_hotels_name",
            "name",
        ),
        Index(
            "ix_hotels_city_status",
            "city_id",
            "status",
        ),
        Index(
            "ix_hotels_star_rating",
            "star_rating",
        ),
    )

    #identificaçao
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(220),
        nullable=False,
        unique=True,
    )

    legal_name: Mapped[str | None] = mapped_column(
        String(250),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    short_description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    #localizaçao
    city_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "cities.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    address_line: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )

    address_number: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    address_complement: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    neighborhood: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    postal_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    latitude: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    #classificaçao
    star_rating: Mapped[Decimal | None] = mapped_column(
        Numeric(
            precision=2,
            scale=1,
        ),
        nullable=True,
    )

    guest_rating: Mapped[Decimal | None] = mapped_column(
        Numeric(
            precision=3,
            scale=2,
        ),
        nullable=True,
    )

    review_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        server_default="0",
    )

    #contatos
    phone: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    website: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    #politicas
    check_in_time: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    check_out_time: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    cancellation_policy: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    #os status  e operaçoes
    status: Mapped[HotelStatus] = mapped_column(
        String(20),
        nullable=False,
        default=HotelStatus.ACTIVE,
        server_default=HotelStatus.ACTIVE.value,
    )

    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    #relacionamentos
    city: Mapped["City"] = relationship(
        "City",
        back_populates="hotels",
        lazy="joined",
    )

    rooms: Mapped[list["Room"]] = relationship(
        "Room",
        back_populates="hotel",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    room_types: Mapped[list["RoomType"]] = relationship(
        "RoomType",
        back_populates="hotel",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    amenities: Mapped[list["Amenity"]] = relationship(
        "Amenity",
        secondary="hotel_amenities",
        back_populates="hotels",
        lazy="selectin",
    )

    images: Mapped[list["Image"]] = relationship(
        "Image",
        back_populates="hotel",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )