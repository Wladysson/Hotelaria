import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class NotificationType(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    recipient: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
        index=True,
    )

    subject: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type"),
        nullable=False,
        index=True,
    )

    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus, name="notification_status"),
        default=NotificationStatus.PENDING,
        nullable=False,
        index=True,
    )

    provider: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    provider_message_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def mark_as_processing(self) -> None:
        self.status = NotificationStatus.PROCESSING

    def mark_as_sent(self, provider_message_id: str | None = None) -> None:
        self.status = NotificationStatus.SENT
        self.provider_message_id = provider_message_id
        self.error_message = None
        self.sent_at = datetime.now(timezone.utc)

    def mark_as_failed(self, error_message: str) -> None:
        self.status = NotificationStatus.FAILED
        self.error_message = error_message