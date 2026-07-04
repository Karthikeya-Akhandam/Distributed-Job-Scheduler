"""Job model — the central work unit with full lifecycle tracking."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Job(Base):
    """An individual unit of work queued for execution by a worker."""

    __tablename__ = "jobs"
    __table_args__ = (
        # Primary claiming query: workers poll for queued jobs ordered by priority
        Index(
            "ix_jobs_claiming",
            "queue_id",
            "status",
            "priority",
            "created_at",
        ),
        # Scheduled job evaluation: find jobs due for execution
        Index("ix_jobs_scheduled", "status", "scheduled_at"),
        # Batch job lookup
        Index(
            "ix_jobs_batch",
            "batch_id",
            postgresql_where="batch_id IS NOT NULL",
        ),
        # Shard-aware claiming
        Index("ix_jobs_shard", "queue_id", "shard_key", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    queue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("queues.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="immediate"
    )  # immediate, delayed, scheduled, recurring, batch
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="queued", index=True
    )  # queued, scheduled, claimed, running, completed, failed, dead, cancelled
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    scheduled_at: Mapped[datetime | None] = mapped_column(nullable=True)
    cron_expression: Mapped[str | None] = mapped_column(String(100), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True
    )
    batch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    shard_key: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Relationships
    queue = relationship("Queue", back_populates="jobs")
    executions = relationship(
        "JobExecution", back_populates="job", cascade="all, delete-orphan"
    )
    logs = relationship("JobLog", back_populates="job", cascade="all, delete-orphan")
    dlq_entries = relationship(
        "DLQEntry", back_populates="job", cascade="all, delete-orphan"
    )
    # Workflow dependencies
    dependencies = relationship(
        "JobDependency",
        foreign_keys="JobDependency.job_id",
        back_populates="job",
        cascade="all, delete-orphan",
    )
    dependents = relationship(
        "JobDependency",
        foreign_keys="JobDependency.depends_on_job_id",
        back_populates="depends_on_job",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Job {self.name} ({self.status})>"
