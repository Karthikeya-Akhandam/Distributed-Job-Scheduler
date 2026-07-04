"""Queue schemas — configuration, statistics, and CRUD."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.common import BaseSchema


# ── Retry Policy ─────────────────────────────────────────────


class RetryPolicyCreateRequest(BaseSchema):
    """Request body for creating a retry policy."""

    name: str = Field(..., min_length=1, max_length=100)
    strategy: str = Field(default="exponential", pattern=r"^(fixed|linear|exponential)$")
    max_retries: int = Field(default=3, ge=0, le=20)
    initial_delay_ms: int = Field(default=1000, ge=100, le=3600000)
    backoff_multiplier: float = Field(default=2.0, ge=1.0, le=10.0)
    max_delay_ms: int = Field(default=300000, ge=1000, le=86400000)


class RetryPolicyResponse(BaseSchema):
    """Retry policy data returned by the API."""

    id: uuid.UUID
    name: str
    strategy: str
    max_retries: int
    initial_delay_ms: int
    backoff_multiplier: float
    max_delay_ms: int
    created_at: datetime


# ── Queue ────────────────────────────────────────────────────


class QueueCreateRequest(BaseSchema):
    """Request body for creating a queue."""

    name: str = Field(..., min_length=1, max_length=100)
    priority: int = Field(default=5, ge=1, le=10)
    concurrency_limit: int = Field(default=10, ge=1, le=1000)
    retry_policy_id: uuid.UUID | None = None
    max_rate_per_minute: int | None = Field(default=None, ge=1, le=100000)
    shard_count: int = Field(default=1, ge=1, le=64)
    metadata: dict[str, Any] | None = None


class QueueUpdateRequest(BaseSchema):
    """Request body for updating queue configuration."""

    priority: int | None = Field(None, ge=1, le=10)
    concurrency_limit: int | None = Field(None, ge=1, le=1000)
    retry_policy_id: uuid.UUID | None = None
    max_rate_per_minute: int | None = Field(None, ge=1, le=100000)
    shard_count: int | None = Field(None, ge=1, le=64)
    metadata: dict[str, Any] | None = None


class QueueResponse(BaseSchema):
    """Queue data returned by the API."""

    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    priority: int
    concurrency_limit: int
    retry_policy_id: uuid.UUID | None
    status: str
    max_rate_per_minute: int | None
    shard_count: int
    metadata: dict[str, Any] | None = None
    created_at: datetime
    retry_policy: RetryPolicyResponse | None = None


class QueueStatsResponse(BaseSchema):
    """Queue statistics snapshot."""

    queue_id: uuid.UUID
    queue_name: str
    total_jobs: int = 0
    queued: int = 0
    running: int = 0
    completed: int = 0
    failed: int = 0
    dead: int = 0
    avg_execution_time_ms: float | None = None
    throughput_per_minute: float | None = None
