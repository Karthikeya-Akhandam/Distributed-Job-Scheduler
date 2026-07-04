"""Worker monitoring API endpoints."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.core.exceptions import BadRequestException, NotFoundException
from app.dependencies import DbSession, get_current_user_dep
from app.models.user import User
from app.models.worker import Worker, WorkerHeartbeat
from app.schemas.common import MessageResponse
from app.schemas.worker import WorkerDetailResponse, WorkerHeartbeatResponse, WorkerResponse

router = APIRouter(prefix="/workers", tags=["Workers"])


@router.get("", response_model=list[WorkerResponse])
async def list_workers(
    db: DbSession,
    current_user: User = Depends(get_current_user_dep),
):
    """List all registered workers."""
    result = await db.execute(
        select(Worker).order_by(Worker.last_seen_at.desc())
    )
    workers = result.scalars().all()
    return [WorkerResponse.model_validate(w) for w in workers]


@router.get("/{worker_id}", response_model=WorkerDetailResponse)
async def get_worker(
    worker_id: uuid.UUID,
    db: DbSession,
    current_user: User = Depends(get_current_user_dep),
):
    """Get worker detail with recent heartbeats."""
    result = await db.execute(select(Worker).where(Worker.id == worker_id))
    worker = result.scalar_one_or_none()
    if not worker:
        raise NotFoundException("Worker", str(worker_id))

    # Fetch last 50 heartbeats
    hb_result = await db.execute(
        select(WorkerHeartbeat)
        .where(WorkerHeartbeat.worker_id == worker_id)
        .order_by(WorkerHeartbeat.heartbeat_at.desc())
        .limit(50)
    )
    heartbeats = hb_result.scalars().all()

    response = WorkerDetailResponse.model_validate(worker)
    response.recent_heartbeats = [
        WorkerHeartbeatResponse.model_validate(h) for h in heartbeats
    ]
    return response


@router.post("/{worker_id}/drain", response_model=MessageResponse)
async def drain_worker(
    worker_id: uuid.UUID,
    db: DbSession,
    current_user: User = Depends(get_current_user_dep),
):
    """Drain a worker — stop taking new jobs, finish in-flight work."""
    result = await db.execute(select(Worker).where(Worker.id == worker_id))
    worker = result.scalar_one_or_none()
    if not worker:
        raise NotFoundException("Worker", str(worker_id))

    if worker.status == "offline":
        raise BadRequestException("Cannot drain an offline worker")

    worker.status = "draining"
    await db.flush()
    return MessageResponse(message=f"Worker '{worker.hostname}' set to draining")
