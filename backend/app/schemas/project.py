"""Project schemas — CRUD operations within an organization."""

import uuid
from datetime import datetime

from pydantic import Field

from app.schemas.common import BaseSchema


class ProjectCreateRequest(BaseSchema):
    """Request body for creating a project."""

    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: str | None = None


class ProjectUpdateRequest(BaseSchema):
    """Request body for updating a project."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None


class ProjectResponse(BaseSchema):
    """Project data returned by the API."""

    id: uuid.UUID
    org_id: uuid.UUID
    name: str
    slug: str
    description: str | None
    created_at: datetime
    queue_count: int | None = None
