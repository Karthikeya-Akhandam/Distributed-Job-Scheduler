"""JobExecution model — tracks individual execution attempts of a job."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class JobExecution(Base):
    """A single execution attempt of a job, recording outcome and metrics."""

    __tablename__ = "job_executions"
    __table_args__ = (
        # Fast lookup of execution history for a job
        {"comment": "Tracks individual execution attempts per job"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    worker_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workers.id", ondelete="SET NULL"),
        nullable=True,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="running"
    )  # running, completed, failed, timed_out
    started_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    stack_trace: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    job = relationship("Job", back_populates="executions")
    worker = relationship("Worker", back_populates="executions")

    def __repr__(self) -> str:
        return f"<JobExecution job={self.job_id} attempt={self.attempt_number} ({self.status})>"
