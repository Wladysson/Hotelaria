import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

if TYPE_CHECKING:
    from src.models.hotel import Hotel


class City(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    """
    Representa uma cidade disponível no catálogo hoteleiro.
    """

    __tablename__ = "cities"

    __table_args__ = (
        Index(
            "ix_cities_country_code_state_code",
            "country_code",
            "state_code",
        ),
        Index(
            "ix_cities_name",
            "name",
        ),
        Index(
            "ix_cities_slug",
            "slug",
            unique=True,
        ),
        Index(
            "ix_cities_active",
            "is_active",
        ),
    )
    #identificaçao
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(180),
        nullable=False,
        unique=True,
    )
    
    # Localização
    state_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    state_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    country_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    country_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    # Localização geográfica
    latitude: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    #status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    #relacionamento
    hotels: Mapped[list["Hotel"]] = relationship(
        "Hotel",
        back_populates="city",
        lazy="selectin",
    )