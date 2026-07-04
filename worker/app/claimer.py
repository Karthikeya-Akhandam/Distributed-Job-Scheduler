"""Atomic job claiming using SELECT ... FOR UPDATE SKIP LOCKED.

This is the core mechanism that prevents duplicate job execution across
multiple worker instances. SKIP LOCKED means workers don't block each other —
if a row is already locked by another worker, it's simply skipped.
"""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import text, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("djs.worker.claimer")


async def claim_jobs(
    session: AsyncSession,
    worker_id: uuid.UUID,
    max_jobs: int,
    shard_keys: list[int] | None = None,
) -> list[dict]:
    """Atomically claim up to `max_jobs` from the database.

    Uses PostgreSQL's FOR UPDATE SKIP LOCKED to prevent duplicate claims.
    Only claims from active (non-paused) queues.

    Args:
        session: Database session.
        worker_id: UUID of the claiming worker.
        max_jobs: Maximum number of jobs to claim in this batch.
        shard_keys: Optional list of shard keys this worker handles.

    Returns:
        List of claimed job dictionaries with id, queue_id, name, payload, etc.
    """
    # Build the claiming query with raw SQL for precise control
    shard_filter = ""
    params: dict = {"max_jobs": max_jobs, "worker_id": str(worker_id)}

    if shard_keys is not None:
        shard_filter = "AND j.shard_key = ANY(:shard_keys)"
        params["shard_keys"] = shard_keys

    query = text(f"""
        WITH claimable AS (
            SELECT j.id
            FROM jobs j
            JOIN queues q ON q.id = j.queue_id
            WHERE j.status = 'queued'
              AND q.status = 'active'
              AND (j.scheduled_at IS NULL OR j.scheduled_at <= NOW())
              {shard_filter}
            ORDER BY q.priority DESC, j.priority DESC, j.created_at ASC
            LIMIT :max_jobs
            FOR UPDATE OF j SKIP LOCKED
        )
        UPDATE jobs
        SET status = 'claimed',
            updated_at = NOW()
        FROM claimable
        WHERE jobs.id = claimable.id
        RETURNING jobs.id, jobs.queue_id, jobs.name, jobs.type, jobs.payload,
                  jobs.attempt_number, jobs.max_retries, jobs.priority
    """)

    result = await session.execute(query, params)
    rows = result.fetchall()

    claimed = []
    for row in rows:
        claimed.append({
            "id": row.id,
            "queue_id": row.queue_id,
            "name": row.name,
            "type": row.type,
            "payload": row.payload,
            "attempt_number": row.attempt_number,
            "max_retries": row.max_retries,
            "priority": row.priority,
        })

    if claimed:
        logger.info("Claimed %d jobs: %s", len(claimed), [str(j["id"])[:8] for j in claimed])

    return claimed
