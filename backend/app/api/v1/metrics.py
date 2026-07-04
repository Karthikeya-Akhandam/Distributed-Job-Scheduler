"""Metrics and statistics API endpoints."""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.core.rbac import get_project_with_org_check
from app.dependencies import DbSession, get_current_user_dep
from app.models.dlq_entry import DLQEntry
from app.models.job import Job
from app.models.job_execution import JobExecution
from app.models.queue import Queue
from app.models.user import User
from app.models.worker import Worker
from app.schemas.metrics import QueueMetricsResponse, SystemOverviewResponse

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/overview", response_model=SystemOverviewResponse)
async def system_overview(
    db: DbSession,
    current_user: User = Depends(get_current_user_dep),
):
    """Get system-wide metrics snapshot."""
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)

    # Total queues
    queues_count = await db.execute(select(func.count(Queue.id)))
    total_queues = queues_count.scalar() or 0

    # Total jobs
    jobs_count = await db.execute(select(func.count(Job.id)))
    total_jobs = jobs_count.scalar() or 0

    # Active workers (online or busy)
    workers_count = await db.execute(
        select(func.count(Worker.id)).where(Worker.status.in_(["online", "busy"]))
    )
    active_workers = workers_count.scalar() or 0

    # Jobs completed in last hour
    completed_result = await db.execute(
        select(func.count(Job.id)).where(
            Job.status == "completed",
            Job.completed_at >= one_hour_ago,
        )
    )
    completed_last_hour = completed_result.scalar() or 0

    # Jobs failed in last hour
    failed_result = await db.execute(
        select(func.count(JobExecution.id)).where(
            JobExecution.status == "failed",
            JobExecution.finished_at >= one_hour_ago,
        )
    )
    failed_last_hour = failed_result.scalar() or 0

    # DLQ entries count
    dlq_count = await db.execute(
        select(func.count(DLQEntry.id)).where(DLQEntry.status == "dead")
    )
    dlq_entries = dlq_count.scalar() or 0

    # Average execution time
    avg_result = await db.execute(
        select(func.avg(JobExecution.duration_ms)).where(
            JobExecution.status == "completed"
        )
    )
    avg_time = avg_result.scalar()

    return SystemOverviewResponse(
        total_queues=total_queues,
        total_jobs=total_jobs,
        active_workers=active_workers,
        jobs_completed_last_hour=completed_last_hour,
        jobs_failed_last_hour=failed_last_hour,
        dlq_entries=dlq_entries,
        avg_execution_time_ms=round(avg_time, 2) if avg_time else None,
    )


@router.get("/queues/{queue_id}", response_model=QueueMetricsResponse)
async def queue_metrics(
    queue_id: uuid.UUID,
    db: DbSession,
    current_user: User = Depends(get_current_user_dep),
):
    """Get detailed metrics for a specific queue."""
    result = await db.execute(select(Queue).where(Queue.id == queue_id))
    queue = result.scalar_one_or_none()
    if not queue:
        raise NotFoundException("Queue", str(queue_id))

    await get_project_with_org_check(queue.project_id, current_user.id, "view", db)

    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)

    # Queue depth (queued + scheduled)
    depth_result = await db.execute(
        select(func.count(Job.id)).where(
            Job.queue_id == queue_id,
            Job.status.in_(["queued", "scheduled"]),
        )
    )
    queue_depth = depth_result.scalar() or 0

    # Active jobs (claimed + running)
    active_result = await db.execute(
        select(func.count(Job.id)).where(
            Job.queue_id == queue_id,
            Job.status.in_(["claimed", "running"]),
        )
    )
    active_jobs = active_result.scalar() or 0

    # Completed and failed in last hour
    completed_result = await db.execute(
        select(func.count(Job.id)).where(
            Job.queue_id == queue_id,
            Job.status == "completed",
            Job.completed_at >= one_hour_ago,
        )
    )
    completed = completed_result.scalar() or 0

    failed_result = await db.execute(
        select(func.count(JobExecution.id)).where(
            JobExecution.status == "failed",
            JobExecution.finished_at >= one_hour_ago,
            JobExecution.job_id.in_(
                select(Job.id).where(Job.queue_id == queue_id)
            ),
        )
    )
    failed = failed_result.scalar() or 0

    # Throughput per minute
    throughput = completed / 60.0 if completed else 0.0

    # Latency percentiles
    latency_query = (
        select(JobExecution.duration_ms)
        .where(
            JobExecution.status == "completed",
            JobExecution.job_id.in_(select(Job.id).where(Job.queue_id == queue_id)),
            JobExecution.duration_ms.isnot(None),
        )
        .order_by(JobExecution.duration_ms)
    )
    latency_result = await db.execute(latency_query)
    latencies = [row[0] for row in latency_result.all()]

    p50 = _percentile(latencies, 50) if latencies else None
    p95 = _percentile(latencies, 95) if latencies else None
    p99 = _percentile(latencies, 99) if latencies else None

    return QueueMetricsResponse(
        queue_id=queue_id,
        queue_name=queue.name,
        queue_depth=queue_depth,
        active_jobs=active_jobs,
        completed_last_hour=completed,
        failed_last_hour=failed,
        throughput_per_minute=round(throughput, 2),
        p50_latency_ms=p50,
        p95_latency_ms=p95,
        p99_latency_ms=p99,
    )


def _percentile(sorted_data: list[int], pct: int) -> float:
    """Calculate the nth percentile of a sorted list."""
    if not sorted_data:
        return 0.0
    k = (len(sorted_data) - 1) * pct / 100.0
    f = int(k)
    c = f + 1
    if c >= len(sorted_data):
        return float(sorted_data[-1])
    d0 = sorted_data[f] * (c - k)
    d1 = sorted_data[c] * (k - f)
    return round(d0 + d1, 2)
