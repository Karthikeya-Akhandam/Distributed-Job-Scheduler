"""Job schemas — creation, listing, detail, and execution history."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.common import BaseSchema


# ── Job Creation ─────────────────────────────────────────────


class JobCreateRequest(BaseSchema):
    """Request body for creating a job."""

    name: str = Field(..., min_length=1, max_length=200)
    type: str = Field(
        default="immediate",
        pattern=r"^(immediate|delayed|scheduled|recurring)$",
    )
    priority: int = Field(default=5, ge=1, le=10)
    payload: dict[str, Any] | None = None
    max_retries: int | None = Field(default=None, ge=0, le=20)
    scheduled_at: datetime | None = None  # For delayed/scheduled jobs
    cron_expression: str | None = None  # For recurring jobs
    idempotency_key: str | None = Field(None, max_length=255)
    depends_on: list[uuid.UUID] | None = None  # Workflow dependencies


class BatchJobCreateRequest(BaseSchema):
    """Request body for creating a batch of jobs."""

    jobs: list[JobCreateRequest] = Field(..., min_length=1, max_length=100)


# ── Job Responses ────────────────────────────────────────────


class JobResponse(BaseSchema):
    """Job data returned by the API."""

    id: uuid.UUID
    queue_id: uuid.UUID
    name: str
    type: str
    status: str
    priority: int
    payload: dict[str, Any] | None
    result: dict[str, Any] | None
    attempt_number: int
    max_retries: int
    scheduled_at: datetime | None
    cron_expression: str | None
    idempotency_key: str | None
    batch_id: uuid.UUID | None
    shard_key: int
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


class JobDetailResponse(JobResponse):
    """Job detail including execution history and dependencies."""

    executions: list["JobExecutionResponse"] = []
    dependencies: list["JobDependencyResponse"] = []


# ── Job Execution ────────────────────────────────────────────


class JobExecutionResponse(BaseSchema):
    """A single execution attempt of a job."""

    id: uuid.UUID
    job_id: uuid.UUID
    worker_id: uuid.UUID | None
    attempt_number: int
    status: str
    started_at: datetime
    finished_at: datetime | None
    duration_ms: int | None
    error_message: str | None
    stack_trace: str | None
    result: dict[str, Any] | None


# ── Job Log ──────────────────────────────────────────────────


class JobLogResponse(BaseSchema):
    """A structured log entry from job execution."""

    id: uuid.UUID
    job_id: uuid.UUID
    level: str
    message: str
    metadata: dict[str, Any] | None = None
    created_at: datetime


# ── Job Dependency ───────────────────────────────────────────


class JobDependencyResponse(BaseSchema):
    """A dependency edge in the job workflow DAG."""

    id: uuid.UUID
    job_id: uuid.UUID
    depends_on_job_id: uuid.UUID
    status: str


# ── DLQ ──────────────────────────────────────────────────────


class DLQEntryResponse(BaseSchema):
    """A dead letter queue entry."""

    id: uuid.UUID
    job_id: uuid.UUID
    queue_id: uuid.UUID
    failure_reason: str
    ai_summary: str | None
    total_attempts: int
    last_error: dict[str, Any] | None
    dead_at: datetime
    retried_at: datetime | None
    status: str


# Rebuild forward refs for nested models
JobDetailResponse.model_rebuild()
