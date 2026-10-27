import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.models.notification import NotificationStatus, NotificationType


class NotificationCreate(BaseModel):
    recipient: str = Field(..., min_length=1, max_length=320)
    subject: str | None = Field(default=None, max_length=255)
    content: str = Field(..., min_length=1)
    notification_type: NotificationType
    provider: str | None = Field(default=None, max_length=100)


class NotificationUpdate(BaseModel):
    status: NotificationStatus | None = None
    provider: str | None = Field(default=None, max_length=100)
    provider_message_id: str | None = Field(default=None, max_length=255)
    error_message: str | None = None


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    recipient: str
    subject: str | None
    content: str
    notification_type: NotificationType
    status: NotificationStatus
    provider: str | None
    provider_message_id: str | None
    error_message: str | None
    sent_at: datetime | None
    created_at: datetime
    updated_at: datetime