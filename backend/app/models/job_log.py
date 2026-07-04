"""JobLog model — structured log entries produced during job execution."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class JobLog(Base):
    """A structured log entry emitted during job execution."""

    __tablename__ = "job_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    level: Mapped[str] = mapped_column(
        String(10), nullable=False, default="info"
    )  # info, warn, error, debug
    message: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    # Relationships
    job = relationship("Job", back_populates="logs")

    def __repr__(self) -> str:
        return f"<JobLog {self.level}: {self.message[:50]}>"
