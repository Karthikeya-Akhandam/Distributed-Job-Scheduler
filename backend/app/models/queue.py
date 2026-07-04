"""Queue model — job container with priority, concurrency, and rate limiting."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Queue(Base):
    """A named queue within a project that holds and processes jobs."""

    __tablename__ = "queues"
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_queue_project_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    priority: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5
    )  # 1-10, higher = processed first
    concurrency_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    retry_policy_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("retry_policies.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # active, paused, draining
    max_rate_per_minute: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # rate limiting: null = unlimited
    shard_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )  # queue sharding
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    # Relationships
    project = relationship("Project", back_populates="queues")
    retry_policy = relationship("RetryPolicy", back_populates="queues")
    jobs = relationship("Job", back_populates="queue", cascade="all, delete-orphan")
    scheduled_jobs = relationship(
        "ScheduledJob", back_populates="queue", cascade="all, delete-orphan"
    )
    dlq_entries = relationship(
        "DLQEntry", back_populates="queue", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Queue {self.name} (priority={self.priority}, status={self.status})>"
