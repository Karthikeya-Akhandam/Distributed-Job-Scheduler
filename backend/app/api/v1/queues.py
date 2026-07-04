"""Queue management API endpoints — CRUD, pause/resume, statistics."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select

from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.core.rbac import get_project_with_org_check
from app.dependencies import DbSession, Pagination, get_current_user_dep
from app.models.job import Job
from app.models.job_execution import JobExecution
from app.models.queue import Queue
from app.models.retry_policy import RetryPolicy
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse, create_pagination_meta
from app.schemas.queue import (
    QueueCreateRequest,
    QueueResponse,
    QueueStatsResponse,
    QueueUpdateRequest,
    RetryPolicyCreateRequest,
    RetryPolicyResponse,
)

router = APIRouter(tags=["Queues"])


# ── Retry Policies ───────────────────────────────────────────


@router.post("/retry-policies", response_model=RetryPolicyResponse, status_code=201)
async def create_retry_policy(
    request: RetryPolicyCreateRequest,
    db: DbSession,
    current_user: User = Depends(get_current_user_dep),
):
    """Create a reusable retry policy."""
    policy = RetryPolicy(
        name=request.name,
        strategy=request.strategy,
        max_retries=request.max_retries,
        initial_delay_ms=request.initial_delay_ms,
        backoff_multiplier=request.backoff_multiplier,
        max_delay_ms=request.max_delay_ms,
    )
    db.add(policy)
    await db.flush()
    return RetryPolicyResponse.model_validate(policy)


@router.get("/retry-policies", response_model=list[RetryPolicyResponse])
async def list_retry_policies(
    db: DbSession,
    current_user: User = Depends(get_current_user_dep),
):
    """List all available retry policies."""
    result = await db.execute(select(RetryPolicy).order_by(RetryPolicy.created_at))
    policies = result.scalars().all()
    return [RetryPolicyResponse.model_validate(p) for p in policies]


# ── Queues ───────────────────────────────────────────────────


@router.post(
    "/projects/{project_id}/queues", response_model=QueueResponse, status_code=201
)
async def create_queue(
    project_id: uuid.UUID,
    request: QueueCreateRequest,
    db: DbSession,
    current_user: User = Depends(get_current_user_dep),
):
    """Create a new queue within a project (requires member+ role)."""
    project = await get_project_with_org_check(
        project_id, current_user.id, "manage_queues", db
    )

    # Check name uniqueness within project
    existing = await db.execute(
        select(Queue).where(Queue.project_id == project_id, Queue.name == request.name)
    )
    if existing.scalar_one_or_none():
        raise ConflictException(
            f"Queue '{request.name}' already exists in this project"
        )

    queue = Queue(
        project_id=project_id,
        name=request.name,
        priority=request.priority,
        concurrency_limit=request.concurrency_limit,
        retry_policy_id=request.retry_policy_id,
        max_rate_per_minute=request.max_rate_per_minute,
        shard_count=request.shard_count,
        metadata_=request.metadata,
    )
    db.add(queue)
    await db.flush()
    return QueueResponse.model_validate(queue)


@router.get("/projects/{project_id}/queues", response_model=PaginatedResponse)
async def list_queues(
    project_id: uuid.UUID,
    db: DbSession,
    pagination: Pagination,
    current_user: User = Depends(get_current_user_dep),
):
    """List queues in a project with basic stats."""
    await get_project_with_org_check(project_id, current_user.id, "view", db)

    base_query = select(Queue).where(Queue.project_id == project_id)

    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        base_query.order_by(Queue.priority.desc(), Queue.created_at)
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )
    queues = result.scalars().all()

    return PaginatedResponse(
        data=[QueueResponse.model_validate(q) for q in queues],
        pagination=create_pagination_meta(pagination.page, pagination.page_size, total),
    )


@router.get("/queues/{queue_id}", response_model=QueueResponse)
async def get_queue(
    queue_id: uuid.UUID,
    db: DbSession,
    current_user: User = Depends(get_current_user_dep),
):
    """Get queue details including retry policy."""
    result = await db.execute(select(Queue).where(Queue.id == queue_id))
    queue = result.scalar_one_or_none()
    if not queue:
        raise NotFoundException("Queue", str(queue_id))

    await get_project_with_org_check(queue.project_id, current_user.id, "view", db)

    # Load retry policy if set
    retry_policy = None
    if queue.retry_policy_id:
        rp_result = await db.execute(
            select(RetryPolicy).where(RetryPolicy.id == queue.retry_policy_id)
        )
        retry_policy = rp_result.scalar_one_or_none()

    response = QueueResponse.model_validate(queue)
    if retry_policy:
        response.retry_policy = RetryPolicyResponse.model_validate(retry_policy)
    return response


@router.patch("/queues/{queue_id}", response_model=QueueResponse)
async def update_queue(
    queue_id: uuid.UUID,
    request: QueueUpdateRequest,
    db: DbSession,
    current_user: User = Depends(get_current_user_dep),
):
    """Update queue configuration (requires member+ role)."""
    result = await db.execute(select(Queue).where(Queue.id == queue_id))
    queue = result.scalar_one_or_none()
    if not queue:
        raise NotFoundException("Queue", str(queue_id))

    await get_project_with_org_check(
        queue.project_id, current_user.id, "manage_queues", db
    )

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "metadata":
            queue.metadata_ = value
        else:
            setattr(queue, key, value)

    await db.flush()
    return QueueResponse.model_validate(queue)


@router.post("/queues/{queue_id}/pause", response_model=MessageResponse)
async def pause_queue(
    queue_id: uuid.UUID,
    db: DbSession,
    current_user: User = Depends(get_current_user_dep),
):
    """Pause a queue — workers will stop claiming new jobs from it."""
    result = await db.execute(select(Queue).where(Queue.id == queue_id))
    queue = result.scalar_one_or_none()
    if not queue:
        raise NotFoundException("Queue", str(queue_id))

    await get_project_with_org_check(
        queue.project_id, current_user.id, "manage_queues", db
    )

    if queue.status == "paused":
        raise BadRequestException("Queue is already paused")

    queue.status = "paused"
    await db.flush()
    return MessageResponse(message=f"Queue '{queue.name}' paused successfully")


@router.post("/queues/{queue_id}/resume", response_model=MessageResponse)
async def resume_queue(
    queue_id: uuid.UUID,
    db: DbSession,
    current_user: User = Depends(get_current_user_dep),
):
    """Resume a paused queue."""
    result = await db.execute(select(Queue).where(Queue.id == queue_id))
    queue = result.scalar_one_or_none()
    if not queue:
        raise NotFoundException("Queue", str(queue_id))

    await get_project_with_org_check(
        queue.project_id, current_user.id, "manage_queues", db
    )

    if queue.status != "paused":
        raise BadRequestException("Queue is not paused")

    queue.status = "active"
    await db.flush()
    return MessageResponse(message=f"Queue '{queue.name}' resumed successfully")


@router.get("/queues/{queue_id}/stats", response_model=QueueStatsResponse)
async def get_queue_stats(
    queue_id: uuid.UUID,
    db: DbSession,
    current_user: User = Depends(get_current_user_dep),
):
    """Get queue statistics: job counts by status, average execution time."""
    result = await db.execute(select(Queue).where(Queue.id == queue_id))
    queue = result.scalar_one_or_none()
    if not queue:
        raise NotFoundException("Queue", str(queue_id))

    await get_project_with_org_check(queue.project_id, current_user.id, "view", db)

    # Count jobs by status
    status_counts = await db.execute(
        select(
            func.count().label("total"),
            func.count().filter(Job.status == "queued").label("queued"),
            func.count().filter(Job.status == "running").label("running"),
            func.count().filter(Job.status == "completed").label("completed"),
            func.count().filter(Job.status == "failed").label("failed"),
            func.count().filter(Job.status == "dead").label("dead"),
        ).where(Job.queue_id == queue_id)
    )
    counts = status_counts.one()

    # Average execution time
    avg_result = await db.execute(
        select(func.avg(JobExecution.duration_ms)).where(
            JobExecution.job_id.in_(
                select(Job.id).where(Job.queue_id == queue_id)
            ),
            JobExecution.status == "completed",
        )
    )
    avg_time = avg_result.scalar()

    return QueueStatsResponse(
        queue_id=queue_id,
        queue_name=queue.name,
        total_jobs=counts.total,
        queued=counts.queued,
        running=counts.running,
        completed=counts.completed,
        failed=counts.failed,
        dead=counts.dead,
        avg_execution_time_ms=round(avg_time, 2) if avg_time else None,
    )
