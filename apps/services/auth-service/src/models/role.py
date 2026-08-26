from uuid import UUID

from sqlalchemy import String, Table, Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id",
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
    Column(
        "role_id",
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "roles.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
)


role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id",
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "roles.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
    Column(
        "permission_id",
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "permissions.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
)


class Role(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    users: Mapped[list["User"]] = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles",
    )

    permissions: Mapped[list["Permission"]] = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
    )