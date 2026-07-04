"""Scheduled job and recurring (cron) job evaluation loops."""

import asyncio
import logging
from datetime import datetime, timezone

from croniter import croniter
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.job import Job
from app.models.scheduled_job import ScheduledJob
from app.models.queue import Queue

logger = logging.getLogger("djs.scheduler")


async def evaluate_scheduled_jobs(session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Evaluate delayed/scheduled/recurring jobs and transition them to 'queued' when ready.

    Also evaluates ScheduledJob templates (recurring cron triggers) to create new Job rows.
    """
    await evaluate_delayed_jobs(session_factory)
    await evaluate_cron_triggers(session_factory)


async def evaluate_delayed_jobs(session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Find scheduled/delayed jobs whose execution time has arrived, and queue them."""
    async with session_factory() as session:
        now = datetime.now(timezone.utc)
        
        # Select all jobs that are 'scheduled' and scheduled_at has passed
        stmt = (
            select(Job)
            .where(Job.status == "scheduled", Job.scheduled_at <= now)
        )
        result = await session.execute(stmt)
        jobs = result.scalars().all()
        
        for job in jobs:
            # Check workflow dependencies before queuing
            dependencies_satisfied = await check_dependencies(session, job.id)
            if dependencies_satisfied:
                job.status = "queued"
                job.updated_at = now
                logger.info("Delayed job %s (%s) transitioned to queued", str(job.id)[:8], job.name)
            
        await session.commit()


async def evaluate_cron_triggers(session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Find active cron templates whose next_run_at has passed, trigger them, and calculate next runtime."""
    async with session_factory() as session:
        now = datetime.now(timezone.utc)
        
        # SELECT ... FOR UPDATE to prevent multiple nodes/threads from evaluating the same cron definition concurrently
        stmt = (
            select(ScheduledJob)
            .where(ScheduledJob.status == "active", ScheduledJob.next_run_at <= now)
            .with_for_update(skip_locked=True)
        )
        result = await session.execute(stmt)
        sched_jobs = result.scalars().all()
        
        for sj in sched_jobs:
            logger.info("Triggering scheduled cron job template %s", str(sj.id)[:8])
            
            # Create a new Job instance from the template
            new_job = Job(
                queue_id=sj.queue_id,
                name=sj.job_template.get("name", "Cron Job"),
                type="recurring",
                status="queued",
                priority=sj.job_template.get("priority", 5),
                payload=sj.job_template.get("payload", {}),
                max_retries=sj.job_template.get("max_retries", 3),
            )
            session.add(new_job)
            
            # Update scheduled job stats and calculate next execution time
            sj.last_run_at = now
            iter_cron = croniter(sj.cron_expression, now)
            sj.next_run_at = iter_cron.get_next(datetime)
            
        await session.commit()


async def check_dependencies(session: AsyncSession, job_id: str) -> bool:
    """Check if all parent workflow dependencies for this job have been satisfied (completed)."""
    # Import JobDependency within function to avoid circular imports
    from app.models.job_dependency import JobDependency
    
    stmt = select(JobDependency).where(JobDependency.job_id == job_id)
    result = await session.execute(stmt)
    deps = result.scalars().all()
    
    for dep in deps:
        if dep.status != "satisfied":
            return False
            
    return True
