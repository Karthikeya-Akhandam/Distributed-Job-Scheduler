"""Organization schemas — CRUD and member management."""

import uuid
from datetime import datetime

from pydantic import EmailStr, Field

from app.schemas.common import BaseSchema


class OrgCreateRequest(BaseSchema):
    """Request body for creating an organization."""

    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")


class OrgResponse(BaseSchema):
    """Organization data returned by the API."""

    id: uuid.UUID
    name: str
    slug: str
    created_at: datetime
    member_count: int | None = None


class OrgMemberResponse(BaseSchema):
    """Organization member with their role."""

    id: uuid.UUID
    user_id: uuid.UUID
    org_id: uuid.UUID
    role: str
    joined_at: datetime
    user_email: str | None = None
    user_name: str | None = None


class AddMemberRequest(BaseSchema):
    """Request to add a member to an organization."""

    email: EmailStr
    role: str = Field(default="member", pattern=r"^(owner|admin|member|viewer)$")


class UpdateMemberRoleRequest(BaseSchema):
    """Request to change a member's role."""

    role: str = Field(..., pattern=r"^(owner|admin|member|viewer)$")
