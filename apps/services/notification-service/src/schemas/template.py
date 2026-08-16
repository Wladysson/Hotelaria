import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    subject_template: str | None = Field(default=None, max_length=255)
    content_template: str = Field(..., min_length=1)
    notification_type: str = Field(..., min_length=1, max_length=20)
    is_active: bool = True


class TemplateUpdate(BaseModel):
    description: str | None = Field(default=None, max_length=255)
    subject_template: str | None = Field(default=None, max_length=255)
    content_template: str | None = Field(default=None, min_length=1)
    notification_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
    )
    is_active: bool | None = None


class TemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    subject_template: str | None
    content_template: str
    notification_type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime