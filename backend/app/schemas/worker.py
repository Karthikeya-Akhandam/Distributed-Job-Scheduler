"""Worker schemas — registration, status, heartbeat."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.common import BaseSchema


class WorkerResponse(BaseSchema):
    """Worker data returned by the API."""

    id: uuid.UUID
    hostname: str
    status: str
    current_load: int
    max_concurrency: int
    capabilities: dict[str, Any] | None
    registered_at: datetime
    last_seen_at: datetime


class WorkerDetailResponse(WorkerResponse):
    """Worker detail including recent heartbeats."""

    recent_heartbeats: list["WorkerHeartbeatResponse"] = []


class WorkerHeartbeatResponse(BaseSchema):
    """A heartbeat entry from a worker."""

    id: uuid.UUID
    worker_id: uuid.UUID
    active_jobs: int
    cpu_usage: float | None
    memory_usage: float | None
    heartbeat_at: datetime


# Rebuild forward refs
WorkerDetailResponse.model_rebuild()
