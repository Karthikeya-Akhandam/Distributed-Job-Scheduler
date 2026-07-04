"""DLQEntry model — Dead Letter Queue for permanently failed jobs."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DLQEntry(Base):
    """A dead-letter entry for a job that exhausted all retry attempts."""

    __tablename__ = "dlq_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    queue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("queues.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    failure_reason: Mapped[str] = mapped_column(Text, nullable=False)
    ai_summary: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # AI-generated failure analysis
    total_attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    last_error: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    dead_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    retried_at: Mapped[datetime | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="dead"
    )  # dead, retried, discarded

    # Relationships
    job = relationship("Job", back_populates="dlq_entries")
    queue = relationship("Queue", back_populates="dlq_entries")

    def __repr__(self) -> str:
        return f"<DLQEntry job={self.job_id} ({self.status})>"
