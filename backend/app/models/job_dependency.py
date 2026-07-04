"""JobDependency model — workflow DAG edges between jobs."""

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class JobDependency(Base):
    """An edge in the job workflow DAG: job_id depends on depends_on_job_id."""

    __tablename__ = "job_dependencies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    depends_on_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending, satisfied, failed

    # Relationships
    job = relationship(
        "Job", foreign_keys=[job_id], back_populates="dependencies"
    )
    depends_on_job = relationship(
        "Job", foreign_keys=[depends_on_job_id], back_populates="dependents"
    )

    def __repr__(self) -> str:
        return f"<JobDependency {self.job_id} -> {self.depends_on_job_id} ({self.status})>"
