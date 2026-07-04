"""Job management API endpoints — creation, lifecycle, logs, and DLQ."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.core.rbac import get_project_with_org_check
from app.dependencies import DbSession, Pagination, get_current_user_dep
from app.models.dlq_entry import DLQEntry
from app.models.job import Job
from app.models.job_dependency import JobDependency
from app.models.job_execution import JobExecution
from app.models.job_log import JobLog
from app.models.queue import Queue
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse, create_pagination_meta
from app.schemas.job import (
    BatchJobCreateRequest,
    DLQEntryResponse,
    JobCreateRequest,
    JobDetailResponse,
    JobDependencyResponse,
    JobExecutionResponse,
    JobLogResponse,
    JobResponse,
)

router = APIRouter(tags=["Jobs"])


# ── Helper ───────────────────────────────────────────────────


async def _get_queue_with_auth(
    queue_id: uuid.UUID, user_id: uuid.UUID, action: str, db: AsyncSession
) -> Queue:
    """Fetch a queue and verify the user has permission."""
    result = await db.execute(select(Queue).where(Queue.id == queue_id))
    queue = result.scalar_one_or_none()
    if not queue:
        raise NotFoundException("Queue", str(queue_id))

    await get_project_with_org_check(queue.project_id, user_id, action, db)
    return queue


def _calculate_shard_key(job_id: uuid.UUID, shard_count: int) -> int:
    """Determine shard assignment for a job."""
    if shard_count <= 1:
        return 0
    return job_id.int % shard_count


# ── Job Creation ─────────────────────────────────────────────


@router.post("/queues/{queue_id}/jobs", response_model=JobResponse, status_code=201)
async def create_job(
    queue_id: uuid.UUID,
    request: JobCreateRequest,
    db: DbSession,
    current_user: User = Depends(get_current_user_dep),
):
    """Create a new job in a queue."""
    queue = await _get_queue_with_auth(queue_id, current_user.id, "manage_jobs", db)

    # Determine initial status based on type
    initial_status = "queued"
    if request.type == "delayed" and request.scheduled_at:
        initial_status = "scheduled"
    elif request.type == "scheduled" and request.scheduled_at:
        initial_status = "scheduled"
    elif request.type == "recurring" and request.cron_expression:
        initial_status = "scheduled"

    # Get max_retries from queue retry policy if not specified
    max_retries = request.max_retries if request.max_retries is not None else 3

    job = Job(
        queue_id=queue_id,
        name=request.name,
        type=request.type,
        status=initial_status,
        priority=request.priority,
        payload=request.payload,
        max_retries=max_retries,
        scheduled_at=request.scheduled_at,
        cron_expression=request.cron_expression,
        idempotency_key=request.idempotency_key,
    )

    # Assign shard key
    db.add(job)
    await db.flush()
    job.shard_key = _calculate_shard_key(job.id, queue.shard_count)

    # Handle workflow dependencies
    if request.depends_on:
        # If job has unresolved dependencies, mark as scheduled (waiting)
        job.status = "scheduled"
        for dep_id in request.depends_on:
            # Verify dependency job exists
            dep_result = await db.execute(select(Job).where(Job.id == dep_id))
            dep_job = dep_result.scalar_one_or_none()
            if not dep_job:
                raise BadRequestException(f"Dependency job '{dep_id}' not found")

            dep_status = "satisfied" if dep_job.status == "completed" else "pending"
            dependency = JobDependency(
                job_id=job.id,
                depends_on_job_id=dep_id,
                status=dep_status,
            )
            db.add(dependency)

    await db.flush()
    return JobResponse.model_validate(job)


@router.post(
    "/queues/{queue_id}/jobs/batch",
    response_model=list[JobResponse],
    status_code=201,
)
async def create_batch_jobs(
    queue_id: uuid.UUID,
    request: BatchJobCreateRequest,
    db: DbSession,
    current_user: User = Depends(get_current_user_dep),
):
    """Create a batch of jobs in a queue."""
    queue = await _get_queue_with_auth(queue_id, current_user.id, "manage_jobs", db)

    batch_id = uuid.uuid4()
    created_jobs = []

    for job_req in request.jobs:
        job = Job(
            queue_id=queue_id,
            name=job_req.name,
            type="batch",
            status="queued",
            priority=job_req.priority,
            payload=job_req.payload,
            max_retries=job_req.max_retries or 3,
            batch_id=batch_id,
        )
        db.add(job)
        await db.flush()
        job.shard_key = _calculate_shard_key(job.id, queue.shard_count)
        created_jobs.append(job)

    await db.flush()
    return [JobResponse.model_validate(j) for j in created_jobs]


# ── Job Listing & Detail ────────────────────────────────────


@router.get("/queues/{queue_id}/jobs", response_model=PaginatedResponse)
async def list_jobs(
    queue_id: uuid.UUID,
    db: DbSession,
    pagination: Pagination,
    current_user: User = Depends(get_current_user_dep),
    status: str | None = Query(None, description="Filter by status"),
    type: str | None = Query(None, description="Filter by job type"),
):
    """List jobs in a queue with optional filtering."""
    await _get_queue_with_auth(queue_id, current_user.id, "view", db)

    base_query = select(Job).where(Job.queue_id == queue_id)
    if status:
        base_query = base_query.where(Job.status == status)
    if type:
        base_query = base_query.where(Job.type == type)

    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        base_query.order_by(Job.priority.desc(), Job.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )
    jobs = result.scalars().all()

    return PaginatedResponse(
        data=[JobResponse.model_validate(j) for j in jobs],
        pagination=create_pagination_meta(pagination.page, pagination.page_size, total),
    )


@router.get("/jobs/{job_id}", response_model=JobDetailResponse)
async def get_job(
    job_id: uuid.UUID,
    db: DbSession,
    current_user: User = Depends(get_current_user_dep),
):
    """Get job details with execution history and dependencies."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundException("Job", str(job_id))

    await _get_queue_with_auth(job.queue_id, current_user.id, "view", db)

    # Fetch executions
    exec_result = await db.execute(
        select(JobExecution)
        .where(JobExecution.job_id == job_id)
        .order_by(JobExecution.attempt_number)
    )
    executions = exec_result.scalars().all()

    # Fetch dependencies
    dep_result = await db.execute(
        select(JobDependency).where(JobDependency.job_id == job_id)
    )
    dependencies = dep_result.scalars().all()

    response = JobDetailResponse.model_validate(job)
    response.executions = [JobExecutionResponse.model_validate(e) for e in executions]
    response.dependencies = [JobDependencyResponse.model_validate(d) for d in dependencies]
    return response


# ── Job Lifecycle ────────────────────────────────────────────


@router.delete("/jobs/{job_id}", response_model=MessageResponse)
async def cancel_job(
    job_id: uuid.UUID,
    db: DbSession,
    current_user: User = Depends(get_current_user_dep),
):
    """Cancel a pending/queued job."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundException("Job", str(job_id))

    await _get_queue_with_auth(job.queue_id, current_user.id, "manage_jobs", db)

    if job.status not in ("queued", "scheduled"):
        raise BadRequestException(
            f"Cannot cancel job in '{job.status}' status. Only queued/scheduled jobs can be cancelled."
        )

    job.status = "cancelled"
    await db.flush()
    return MessageResponse(message=f"Job '{job.name}' cancelled successfully")


@router.post("/jobs/{job_id}/retry", response_model=JobResponse)
async def retry_job(
    job_id: uuid.UUID,
    db: DbSession,
    current_user: User = Depends(get_current_user_dep),
):
    """Manually retry a failed or dead job."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundException("Job", str(job_id))

    await _get_queue_with_auth(job.queue_id, current_user.id, "manage_jobs", db)

    if job.status not in ("failed", "dead", "cancelled"):
        raise BadRequestException(
            f"Cannot retry job in '{job.status}' status. Only failed/dead/cancelled jobs can be retried."
        )

    job.status = "queued"
    job.attempt_number = 0
    job.result = None
    job.completed_at = None
    await db.flush()

    return JobResponse.model_validate(job)


# ── Job Logs ─────────────────────────────────────────────────


@router.get("/jobs/{job_id}/logs", response_model=list[JobLogResponse])
async def get_job_logs(
    job_id: uuid.UUID,
    db: DbSession,
    current_user: User = Depends(get_current_user_dep),
):
    """Get execution logs for a job."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundException("Job", str(job_id))

    await _get_queue_with_auth(job.queue_id, current_user.id, "view", db)

    log_result = await db.execute(
        select(JobLog)
        .where(JobLog.job_id == job_id)
        .order_by(JobLog.created_at)
    )
    logs = log_result.scalars().all()
    return [JobLogResponse.model_validate(log) for log in logs]


@router.get("/jobs/{job_id}/executions", response_model=list[JobExecutionResponse])
async def get_job_executions(
    job_id: uuid.UUID,
    db: DbSession,
    current_user: User = Depends(get_current_user_dep),
):
    """Get execution attempts for a job."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundException("Job", str(job_id))

    await _get_queue_with_auth(job.queue_id, current_user.id, "view", db)

    exec_result = await db.execute(
        select(JobExecution)
        .where(JobExecution.job_id == job_id)
        .order_by(JobExecution.attempt_number)
    )
    executions = exec_result.scalars().all()
    return [JobExecutionResponse.model_validate(e) for e in executions]


# ── Dead Letter Queue ────────────────────────────────────────


@router.get("/queues/{queue_id}/dlq", response_model=PaginatedResponse)
async def list_dlq_entries(
    queue_id: uuid.UUID,
    db: DbSession,
    pagination: Pagination,
    current_user: User = Depends(get_current_user_dep),
):
    """List dead letter queue entries for a queue."""
    await _get_queue_with_auth(queue_id, current_user.id, "view", db)

    base_query = select(DLQEntry).where(DLQEntry.queue_id == queue_id)

    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        base_query.order_by(DLQEntry.dead_at.desc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )
    entries = result.scalars().all()

    return PaginatedResponse(
        data=[DLQEntryResponse.model_validate(e) for e in entries],
        pagination=create_pagination_meta(pagination.page, pagination.page_size, total),
    )


@router.post("/dlq/{dlq_id}/retry", response_model=MessageResponse)
async def retry_dlq_entry(
    dlq_id: uuid.UUID,
    db: DbSession,
    current_user: User = Depends(get_current_user_dep),
):
    """Retry a dead letter queue entry — re-enqueues the original job."""
    result = await db.execute(select(DLQEntry).where(DLQEntry.id == dlq_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise NotFoundException("DLQ entry", str(dlq_id))

    await _get_queue_with_auth(entry.queue_id, current_user.id, "manage_jobs", db)

    if entry.status != "dead":
        raise BadRequestException("DLQ entry has already been retried or discarded")

    # Re-enqueue the original job
    job_result = await db.execute(select(Job).where(Job.id == entry.job_id))
    job = job_result.scalar_one_or_none()
    if job:
        job.status = "queued"
        job.attempt_number = 0
        job.result = None
        job.completed_at = None

    entry.status = "retried"
    entry.retried_at = datetime.now(timezone.utc)
    await db.flush()

    return MessageResponse(message="DLQ entry retried — job re-enqueued")


@router.post("/dlq/{dlq_id}/discard", response_model=MessageResponse)
async def discard_dlq_entry(
    dlq_id: uuid.UUID,
    db: DbSession,
    current_user: User = Depends(get_current_user_dep),
):
    """Discard a dead letter queue entry — permanently remove it."""
    result = await db.execute(select(DLQEntry).where(DLQEntry.id == dlq_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise NotFoundException("DLQ entry", str(dlq_id))

    await _get_queue_with_auth(entry.queue_id, current_user.id, "manage_jobs", db)

    if entry.status != "dead":
        raise BadRequestException("DLQ entry has already been retried or discarded")

    entry.status = "discarded"
    await db.flush()

    return MessageResponse(message="DLQ entry discarded")
