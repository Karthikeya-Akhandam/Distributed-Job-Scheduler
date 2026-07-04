"""Job lifecycle state machine — manages transitions between job states."""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import text, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("djs.worker.lifecycle")

# Valid state transitions
VALID_TRANSITIONS = {
    "queued": {"claimed", "cancelled"},
    "scheduled": {"queued", "claimed", "cancelled"},
    "claimed": {"running"},
    "running": {"completed", "failed"},
    "failed": {"queued", "dead"},  # queued = retry, dead = DLQ
    "completed": set(),
    "dead": {"queued"},  # manual retry from DLQ
    "cancelled": {"queued"},  # re-enqueue
}


async def transition_job(
    session: AsyncSession,
    job_id: uuid.UUID,
    from_status: str,
    to_status: str,
    result: dict | None = None,
    error_message: str | None = None,
) -> bool:
    """Atomically transition a job from one status to another.

    Args:
        session: Database session.
        job_id: The job's UUID.
        from_status: Expected current status (for optimistic concurrency).
        to_status: Target status.
        result: Optional result data (for completed jobs).
        error_message: Optional error message (for failed jobs).

    Returns:
        True if the transition succeeded, False if the job was in an unexpected state.
    """
    if to_status not in VALID_TRANSITIONS.get(from_status, set()):
        logger.error(
            "Invalid transition: %s → %s for job %s",
            from_status,
            to_status,
            str(job_id)[:8],
        )
        return False

    now = datetime.now(timezone.utc)
    completed_at = now if to_status == "completed" else None

    query = text("""
        UPDATE jobs
        SET status = :to_status,
            updated_at = :now,
            completed_at = COALESCE(:completed_at, completed_at),
            result = COALESCE(:result, result)
        WHERE id = :job_id AND status = :from_status
        RETURNING id
    """)

    result_row = await session.execute(
        query,
        {
            "to_status": to_status,
            "now": now,
            "completed_at": completed_at,
            "result": result if result else None,
            "job_id": str(job_id),
            "from_status": from_status,
        },
    )

    row = result_row.fetchone()
    if row:
        logger.info("Job %s: %s → %s", str(job_id)[:8], from_status, to_status)
        return True
    else:
        logger.warning(
            "Job %s transition failed: expected status '%s' but job was in a different state",
            str(job_id)[:8],
            from_status,
        )
        return False


async def increment_attempt(session: AsyncSession, job_id: uuid.UUID) -> int:
    """Increment and return the job's attempt counter."""
    query = text("""
        UPDATE jobs SET attempt_number = attempt_number + 1, updated_at = NOW()
        WHERE id = :job_id
        RETURNING attempt_number
    """)
    result = await session.execute(query, {"job_id": str(job_id)})
    row = result.fetchone()
    return row.attempt_number if row else 0
