"""Metrics schemas — system overview and queue-level metrics."""

import uuid
from datetime import datetime

from app.schemas.common import BaseSchema


class SystemOverviewResponse(BaseSchema):
    """System-wide metrics snapshot."""

    total_queues: int
    total_jobs: int
    active_workers: int
    jobs_completed_last_hour: int
    jobs_failed_last_hour: int
    dlq_entries: int
    avg_execution_time_ms: float | None


class QueueMetricsResponse(BaseSchema):
    """Detailed metrics for a specific queue."""

    queue_id: uuid.UUID
    queue_name: str
    # Current state
    queue_depth: int
    active_jobs: int
    # Throughput (last hour)
    completed_last_hour: int
    failed_last_hour: int
    throughput_per_minute: float
    # Latency percentiles (ms)
    p50_latency_ms: float | None
    p95_latency_ms: float | None
    p99_latency_ms: float | None
    # Time series (last 24 data points)
    throughput_history: list[dict] = []  # [{timestamp, completed, failed}]
