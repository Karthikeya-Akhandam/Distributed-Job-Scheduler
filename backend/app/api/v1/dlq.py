"""DLQ-specific API endpoints with AI summary generation."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.core.exceptions import NotFoundException
from app.dependencies import DbSession, get_current_user_dep
from app.models.dlq_entry import DLQEntry
from app.models.job import Job
from app.models.job_execution import JobExecution
from app.models.user import User
from app.schemas.job import DLQEntryResponse
from app.services.ai_summary import generate_failure_summary

router = APIRouter(prefix="/dlq", tags=["Dead Letter Queue"])


@router.get("/{dlq_id}/ai-summary", response_model=DLQEntryResponse)
async def get_ai_summary(
    dlq_id: uuid.UUID,
    db: DbSession,
    current_user: User = Depends(get_current_user_dep),
):
    """Generate or retrieve an AI-powered failure analysis for a DLQ entry.

    If a summary already exists, it is returned immediately.
    Otherwise, one is generated and cached on the entry.
    """
    result = await db.execute(select(DLQEntry).where(DLQEntry.id == dlq_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise NotFoundException("DLQ entry", str(dlq_id))

    # Return cached summary if available
    if not entry.ai_summary:
        # Get job details
        job_result = await db.execute(select(Job).where(Job.id == entry.job_id))
        job = job_result.scalar_one_or_none()
        job_name = job.name if job else "Unknown"

        # Get execution history
        exec_result = await db.execute(
            select(JobExecution)
            .where(JobExecution.job_id == entry.job_id)
            .order_by(JobExecution.attempt_number)
        )
        executions = exec_result.scalars().all()

        history = [
            {
                "attempt": e.attempt_number,
                "status": e.status,
                "error": e.error_message or "N/A",
                "duration_ms": e.duration_ms,
            }
            for e in executions
        ]

        # Generate and cache summary
        summary = await generate_failure_summary(
            job_name=job_name,
            error_message=entry.failure_reason,
            total_attempts=entry.total_attempts,
            execution_history=history,
        )
        entry.ai_summary = summary
        await db.flush()

    return DLQEntryResponse.model_validate(entry)
