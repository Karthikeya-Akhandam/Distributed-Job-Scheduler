"""Common schemas used across the application: pagination, errors, base responses."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(from_attributes=True)


class TimestampMixin(BaseModel):
    """Mixin providing created_at / updated_at fields for response schemas."""

    created_at: datetime
    updated_at: datetime | None = None


# ── Pagination ───────────────────────────────────────────────


class PaginationMeta(BaseModel):
    """Pagination metadata returned with list responses."""

    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


class PaginatedResponse(BaseModel):
    """Generic paginated list response wrapper."""

    data: list
    pagination: PaginationMeta


def create_pagination_meta(page: int, page_size: int, total: int) -> PaginationMeta:
    """Helper to build PaginationMeta from query results."""
    total_pages = max(1, (total + page_size - 1) // page_size)
    return PaginationMeta(
        page=page,
        page_size=page_size,
        total_items=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )


# ── Error Responses ──────────────────────────────────────────


class ErrorDetail(BaseModel):
    """A single error detail."""

    field: str | None = None
    message: str
    code: str | None = None


class ErrorResponse(BaseModel):
    """Standard error response returned by the API."""

    error: str
    message: str
    details: list[ErrorDetail] | None = None
    status_code: int


# ── Generic ID Response ──────────────────────────────────────


class IdResponse(BaseModel):
    """Response containing just an ID (e.g., after creation)."""

    id: uuid.UUID


class MessageResponse(BaseModel):
    """Response containing a simple message."""

    message: str
