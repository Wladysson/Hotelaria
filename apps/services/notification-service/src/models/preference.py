import enum
import uuid

from sqlalchemy import Boolean, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class NotificationChannel(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class NotificationPreference(Base, TimestampMixin):
    __tablename__ = "notification_preferences"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "channel",
            name="uq_notification_preference_user_channel",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(
            NotificationChannel,
            name="notification_channel",
        ),
        nullable=False,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )