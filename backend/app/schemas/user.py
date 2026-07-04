"""User schemas — request and response models for user endpoints."""

import uuid
from datetime import datetime

from pydantic import EmailStr, Field

from app.schemas.common import BaseSchema


class UserResponse(BaseSchema):
    """User data returned by the API (excludes password_hash)."""

    id: uuid.UUID
    email: EmailStr
    name: str
    role: str
    is_active: bool
    created_at: datetime


class UserUpdateRequest(BaseSchema):
    """Request body for updating user profile."""

    name: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = None
