"""Concurrent job executor — runs claimed jobs with asyncio TaskGroup."""

import asyncio
import logging
import traceback
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.handlers.base import get_handler
from app.lifecycle import increment_attempt, transition_job

logger = logging.getLogger("djs.worker.executor")


async def execute_job(
    session_factory: async_sessionmaker[AsyncSession],
    job_data: dict,
    worker_id: uuid.UUID,
) -> None:
    """Execute a single claimed job through its full lifecycle.

    Flow: claimed → running → (completed | failed → retry/DLQ)

    Args:
        session_factory: Factory to create new DB sessions.
        job_data: Dictionary from the claimer with job id, payload, etc.
        worker_id: UUID of the executing worker.
    """
    job_id = job_data["id"]
    job_name = job_data["name"]
    job_type = job_data["type"]
    payload = job_data["payload"]
    attempt = job_data["attempt_number"]
    max_retries = job_data["max_retries"]

    logger.info("Executing job %s (%s) attempt #%d", str(job_id)[:8], job_name, attempt + 1)

    async with session_factory() as session:
        # Transition: claimed → running
        ok = await transition_job(session, job_id, "claimed", "running")
        if not ok:
            logger.warning("Failed to transition job %s to running, aborting", str(job_id)[:8])
            return
        await session.commit()

    # Increment attempt counter
    async with session_factory() as session:
        attempt_num = await increment_attempt(session, job_id)
        await session.commit()

    # Record execution start
    execution_id = uuid.uuid4()
    started_at = datetime.now(timezone.utc)

    async with session_factory() as session:
        from sqlalchemy import text

        await session.execute(
            text("""
                INSERT INTO job_executions (id, job_id, worker_id, attempt_number, status, started_at)
                VALUES (:id, :job_id, :worker_id, :attempt_number, 'running', :started_at)
            """),
            {
                "id": str(execution_id),
                "job_id": str(job_id),
                "worker_id": str(worker_id),
                "attempt_number": attempt_num,
                "started_at": started_at,
            },
        )
        await session.commit()

    # Execute the handler
    handler = get_handler(job_type)
    try:
        result = await handler.execute(payload)
        finished_at = datetime.now(timezone.utc)
        duration_ms = int((finished_at - started_at).total_seconds() * 1000)

        # Success: running → completed
        async with session_factory() as session:
            await transition_job(session, job_id, "running", "completed", result=result)

            # Update execution record
            await session.execute(
                text("""
                    UPDATE job_executions
                    SET status = 'completed', finished_at = :finished_at,
                        duration_ms = :duration_ms, result = :result
                    WHERE id = :exec_id
                """),
                {
                    "finished_at": finished_at,
                    "duration_ms": duration_ms,
                    "result": str(result),
                    "exec_id": str(execution_id),
                },
            )

            # Log success
            await session.execute(
                text("""
                    INSERT INTO job_logs (id, job_id, level, message, created_at)
                    VALUES (:id, :job_id, 'info', :message, :created_at)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "job_id": str(job_id),
                    "message": f"Job completed successfully in {duration_ms}ms (attempt #{attempt_num})",
                    "created_at": finished_at,
                },
            )
            await session.commit()

        logger.info("Job %s completed in %dms", str(job_id)[:8], duration_ms)

    except Exception as exc:
        finished_at = datetime.now(timezone.utc)
        duration_ms = int((finished_at - started_at).total_seconds() * 1000)
        error_msg = str(exc)
        stack = traceback.format_exc()

        logger.error("Job %s failed: %s", str(job_id)[:8], error_msg)

        async with session_factory() as session:
            # Fail the job: running → failed
            await transition_job(session, job_id, "running", "failed")

            # Update execution record
            await session.execute(
                text("""
                    UPDATE job_executions
                    SET status = 'failed', finished_at = :finished_at,
                        duration_ms = :duration_ms, error_message = :error_msg,
                        stack_trace = :stack_trace
                    WHERE id = :exec_id
                """),
                {
                    "finished_at": finished_at,
                    "duration_ms": duration_ms,
                    "error_msg": error_msg,
                    "stack_trace": stack,
                    "exec_id": str(execution_id),
                },
            )

            # Log failure
            await session.execute(
                text("""
                    INSERT INTO job_logs (id, job_id, level, message, created_at)
                    VALUES (:id, :job_id, 'error', :message, :created_at)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "job_id": str(job_id),
                    "message": f"Job failed on attempt #{attempt_num}: {error_msg}",
                    "created_at": finished_at,
                },
            )
            await session.commit()

        # Retry logic
        await _handle_retry_or_dlq(session_factory, job_id, attempt_num, max_retries, error_msg, stack)


async def _handle_retry_or_dlq(
    session_factory: async_sessionmaker[AsyncSession],
    job_id: uuid.UUID,
    attempt: int,
    max_retries: int,
    error_msg: str,
    stack_trace: str,
) -> None:
    """Decide whether to retry a failed job or move it to the DLQ.

    Calculates retry delay using the queue's retry policy and re-enqueues
    with a scheduled_at time, or moves to DLQ if all retries exhausted.
    """
    if attempt < max_retries:
        # Retry: re-enqueue with delay
        from sqlalchemy import text

        async with session_factory() as session:
            # Get retry policy from queue
            result = await session.execute(
                text("""
                    SELECT rp.strategy, rp.initial_delay_ms, rp.backoff_multiplier, rp.max_delay_ms
                    FROM jobs j
                    JOIN queues q ON q.id = j.queue_id
                    LEFT JOIN retry_policies rp ON rp.id = q.retry_policy_id
                    WHERE j.id = :job_id
                """),
                {"job_id": str(job_id)},
            )
            row = result.fetchone()

            # Calculate delay
            strategy = row.strategy if row and row.strategy else "exponential"
            initial_delay = row.initial_delay_ms if row and row.initial_delay_ms else 1000
            multiplier = row.backoff_multiplier if row and row.backoff_multiplier else 2.0
            max_delay = row.max_delay_ms if row and row.max_delay_ms else 300000

            if strategy == "fixed":
                delay_ms = initial_delay
            elif strategy == "linear":
                delay_ms = initial_delay * attempt
            elif strategy == "exponential":
                delay_ms = int(initial_delay * (multiplier ** (attempt - 1)))
            else:
                delay_ms = initial_delay

            delay_ms = min(delay_ms, max_delay)

            # Re-enqueue with scheduled_at
            from datetime import timedelta

            next_run = datetime.now(timezone.utc) + timedelta(milliseconds=delay_ms)

            await transition_job(session, job_id, "failed", "queued")
            await session.execute(
                text("UPDATE jobs SET scheduled_at = :next_run WHERE id = :job_id"),
                {"next_run": next_run, "job_id": str(job_id)},
            )
            await session.commit()

        logger.info(
            "Job %s scheduled for retry #%d in %dms",
            str(job_id)[:8],
            attempt + 1,
            delay_ms,
        )
    else:
        # Move to DLQ
        from sqlalchemy import text

        async with session_factory() as session:
            # Get queue_id
            result = await session.execute(
                text("SELECT queue_id FROM jobs WHERE id = :job_id"),
                {"job_id": str(job_id)},
            )
            row = result.fetchone()
            queue_id = row.queue_id if row else None

            await transition_job(session, job_id, "failed", "dead")

            if queue_id:
                await session.execute(
                    text("""
                        INSERT INTO dlq_entries (id, job_id, queue_id, failure_reason, total_attempts, last_error, dead_at)
                        VALUES (:id, :job_id, :queue_id, :reason, :attempts, :last_error, :dead_at)
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "job_id": str(job_id),
                        "queue_id": str(queue_id),
                        "reason": error_msg,
                        "attempts": attempt,
                        "last_error": f'{{"message": "{error_msg}"}}',
                        "dead_at": datetime.now(timezone.utc),
                    },
                )

            await session.commit()

        logger.warning(
            "Job %s moved to DLQ after %d attempts",
            str(job_id)[:8],
            attempt,
        )
