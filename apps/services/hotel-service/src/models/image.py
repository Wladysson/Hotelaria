from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
    String,
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


class ImageType(str, Enum):
    HOTEL = "hotel"
    ROOM = "room"
    ROOM_TYPE = "room_type"
    GALLERY = "gallery"


class Image(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    """
    Representa uma imagem associada ao catálogo hoteleiro.
    """

    __tablename__ = "images"

    __table_args__ = (
        Index(
            "ix_images_hotel_id",
            "hotel_id",
        ),
        Index(
            "ix_images_type",
            "type",
        ),
        Index(
            "ix_images_hotel_type",
            "hotel_id",
            "type",
        ),
        Index(
            "ix_images_display_order",
            "display_order",
        ),
        Index(
            "ix_images_featured",
            "is_featured",
        ),
    )

    # relacionamento

    hotel_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "hotels.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    # dados das imagens

    url: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    thumbnail_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    alt_text: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # clacisifcaçoes

    type: Mapped[ImageType] = mapped_column(
        String(30),
        nullable=False,
        default=ImageType.HOTEL,
        server_default=ImageType.HOTEL.value,
    )

    # exibiçao

    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    # relacionamento

    hotel: Mapped["Hotel"] = relationship(
        "Hotel",
        back_populates="images",
    )