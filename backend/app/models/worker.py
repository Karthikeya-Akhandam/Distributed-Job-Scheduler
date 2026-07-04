"""Worker and WorkerHeartbeat models — worker registration and health monitoring."""

import uuid
from datetime import datetime

from sqlalchemy import Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Worker(Base):
    """A worker process registered with the system for executing jobs."""

    __tablename__ = "workers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="online"
    )  # online, busy, draining, offline
    current_load: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_concurrency: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    capabilities: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    registered_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    # Relationships
    heartbeats = relationship(
        "WorkerHeartbeat", back_populates="worker", cascade="all, delete-orphan"
    )
    executions = relationship("JobExecution", back_populates="worker")

    def __repr__(self) -> str:
        return f"<Worker {self.hostname} ({self.status})>"


class WorkerHeartbeat(Base):
    """Periodic health report from a worker including system metrics."""

    __tablename__ = "worker_heartbeats"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    worker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    active_jobs: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cpu_usage: Mapped[float | None] = mapped_column(Float, nullable=True)
    memory_usage: Mapped[float | None] = mapped_column(Float, nullable=True)
    heartbeat_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    # Relationships
    worker = relationship("Worker", back_populates="heartbeats")

    def __repr__(self) -> str:
        return f"<WorkerHeartbeat worker={self.worker_id} at={self.heartbeat_at}>"
