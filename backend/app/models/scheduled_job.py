"""ScheduledJob model — recurring and cron-based job definitions."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ScheduledJob(Base):
    """A recurring job definition that periodically creates new Job instances."""

    __tablename__ = "scheduled_jobs"
    __table_args__ = (
        {"comment": "Stores cron definitions; the scheduler evaluates next_run_at periodically"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    queue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("queues.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False)
    job_template: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # active, paused, cancelled
    next_run_at: Mapped[datetime | None] = mapped_column(nullable=True, index=True)
    last_run_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    # Relationships
    queue = relationship("Queue", back_populates="scheduled_jobs")

    def __repr__(self) -> str:
        return f"<ScheduledJob cron={self.cron_expression} ({self.status})>"
