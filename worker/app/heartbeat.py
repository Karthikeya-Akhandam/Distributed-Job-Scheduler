"""Worker heartbeat — periodic health reporting to the database."""

import logging
import uuid
from datetime import datetime, timezone

import psutil
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = logging.getLogger("djs.worker.heartbeat")


async def send_heartbeat(
    session_factory: async_sessionmaker[AsyncSession],
    worker_id: uuid.UUID,
    active_jobs: int,
) -> None:
    """Send a heartbeat to the database with current system metrics.

    Updates the worker's last_seen_at and inserts a heartbeat record
    with CPU usage, memory usage, and active job count.

    Args:
        session_factory: Factory to create DB sessions.
        worker_id: UUID of this worker.
        active_jobs: Number of jobs currently executing.
    """
    try:
        cpu = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory().percent

        async with session_factory() as session:
            now = datetime.now(timezone.utc)

            # Update worker last_seen_at and current_load
            await session.execute(
                text("""
                    UPDATE workers
                    SET last_seen_at = :now,
                        current_load = :load,
                        status = CASE
                            WHEN :load >= max_concurrency THEN 'busy'
                            WHEN status = 'draining' THEN 'draining'
                            ELSE 'online'
                        END
                    WHERE id = :worker_id
                """),
                {"now": now, "load": active_jobs, "worker_id": str(worker_id)},
            )

            # Insert heartbeat record
            await session.execute(
                text("""
                    INSERT INTO worker_heartbeats (id, worker_id, active_jobs, cpu_usage, memory_usage, heartbeat_at)
                    VALUES (:id, :worker_id, :active_jobs, :cpu, :memory, :now)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "worker_id": str(worker_id),
                    "active_jobs": active_jobs,
                    "cpu": cpu,
                    "memory": memory,
                    "now": now,
                },
            )

            await session.commit()

        logger.debug(
            "Heartbeat sent: %d active jobs, CPU %.1f%%, Memory %.1f%%",
            active_jobs,
            cpu,
            memory,
        )

    except Exception:
        logger.exception("Failed to send heartbeat")


async def register_worker(
    session_factory: async_sessionmaker[AsyncSession],
    worker_id: uuid.UUID,
    hostname: str,
    max_concurrency: int,
) -> None:
    """Register this worker in the database on startup.

    If a record with the same ID exists (e.g., after restart), it is updated.
    """
    async with session_factory() as session:
        await session.execute(
            text("""
                INSERT INTO workers (id, hostname, status, max_concurrency, registered_at, last_seen_at)
                VALUES (:id, :hostname, 'online', :max_concurrency, NOW(), NOW())
                ON CONFLICT (id) DO UPDATE
                SET hostname = :hostname,
                    status = 'online',
                    max_concurrency = :max_concurrency,
                    current_load = 0,
                    last_seen_at = NOW()
            """),
            {
                "id": str(worker_id),
                "hostname": hostname,
                "max_concurrency": max_concurrency,
            },
        )
        await session.commit()
    logger.info("Worker registered: %s (%s)", hostname, str(worker_id)[:8])


async def deregister_worker(
    session_factory: async_sessionmaker[AsyncSession],
    worker_id: uuid.UUID,
) -> None:
    """Mark the worker as offline during shutdown."""
    async with session_factory() as session:
        await session.execute(
            text("UPDATE workers SET status = 'offline', current_load = 0 WHERE id = :id"),
            {"id": str(worker_id)},
        )
        await session.commit()
    logger.info("Worker deregistered: %s", str(worker_id)[:8])
