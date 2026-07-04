"""Worker service entry point — orchestrates claiming, executing, heartbeats, and shutdown."""

import asyncio
import logging
import platform
import uuid

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.claimer import claim_jobs
from app.config import get_worker_settings
from app.executor import execute_job
from app.heartbeat import deregister_worker, register_worker, send_heartbeat
from app.shutdown import ShutdownCoordinator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)-7s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("djs.worker")

settings = get_worker_settings()


async def main() -> None:
    """Main worker loop: register → poll → execute → heartbeat → shutdown."""
    worker_id = uuid.uuid5(uuid.NAMESPACE_DNS, settings.worker_id)
    hostname = f"{platform.node()}-{settings.worker_id}"

    logger.info("═══════════════════════════════════════════")
    logger.info("  Distributed Job Scheduler — Worker")
    logger.info("  ID:            %s", settings.worker_id)
    logger.info("  UUID:          %s", str(worker_id)[:8])
    logger.info("  Concurrency:   %d", settings.worker_max_concurrency)
    logger.info("  Poll Interval: %.1fs", settings.worker_poll_interval_seconds)
    logger.info("═══════════════════════════════════════════")

    # Create database engine and session factory
    engine = create_async_engine(
        settings.database_url,
        pool_size=settings.worker_max_concurrency + 5,
        max_overflow=5,
        pool_pre_ping=True,
    )
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create Redis client for pub/sub events
    redis = aioredis.from_url(settings.redis_url, decode_responses=True)

    # Setup shutdown coordination
    shutdown = ShutdownCoordinator()

    # Register worker
    await register_worker(session_factory, worker_id, hostname, settings.worker_max_concurrency)

    # Track active jobs
    active_tasks: set[asyncio.Task] = set()

    async def cleanup_task(task: asyncio.Task) -> None:
        """Remove completed task from tracking set."""
        active_tasks.discard(task)

    # Heartbeat loop
    async def heartbeat_loop():
        while not shutdown.should_shutdown:
            await send_heartbeat(session_factory, worker_id, len(active_tasks))
            await asyncio.sleep(settings.worker_heartbeat_interval_seconds)

    # Main polling loop
    async def poll_loop():
        while not shutdown.should_shutdown:
            available_slots = settings.worker_max_concurrency - len(active_tasks)

            if available_slots > 0:
                try:
                    async with session_factory() as session:
                        jobs = await claim_jobs(session, worker_id, min(available_slots, 5))
                        await session.commit()

                    for job_data in jobs:
                        task = asyncio.create_task(
                            execute_job(session_factory, job_data, worker_id)
                        )
                        active_tasks.add(task)
                        task.add_done_callback(lambda t: active_tasks.discard(t))

                except Exception:
                    logger.exception("Error in polling loop")

            await asyncio.sleep(settings.worker_poll_interval_seconds)

    # Run all loops concurrently
    try:
        # On Windows, signal handlers work differently
        if platform.system() != "Windows":
            shutdown.setup_signal_handlers(asyncio.get_event_loop())

        heartbeat_task = asyncio.create_task(heartbeat_loop())
        poll_task = asyncio.create_task(poll_loop())

        # Wait for shutdown signal or KeyboardInterrupt
        try:
            await shutdown.wait_for_shutdown()
        except (KeyboardInterrupt, SystemExit):
            shutdown.request_shutdown()

        logger.info("Shutdown initiated — waiting for %d in-flight jobs...", len(active_tasks))

        # Cancel polling and heartbeat
        poll_task.cancel()
        heartbeat_task.cancel()

        # Wait for in-flight jobs (with timeout)
        if active_tasks:
            done, pending = await asyncio.wait(active_tasks, timeout=30.0)
            if pending:
                logger.warning("Timed out waiting for %d jobs, cancelling...", len(pending))
                for task in pending:
                    task.cancel()

    finally:
        # Deregister worker
        await deregister_worker(session_factory, worker_id)
        await redis.close()
        await engine.dispose()
        logger.info("Worker shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
