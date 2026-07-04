"""Retry policy model — configurable retry strategies for queues."""

import uuid
from datetime import datetime

from sqlalchemy import Float, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RetryPolicy(Base):
    """Defines a reusable retry strategy for queue job failures."""

    __tablename__ = "retry_policies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    strategy: Mapped[str] = mapped_column(
        String(20), nullable=False, default="exponential"
    )  # fixed, linear, exponential
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    initial_delay_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    backoff_multiplier: Mapped[float] = mapped_column(Float, nullable=False, default=2.0)
    max_delay_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=300000)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    # Relationships
    queues = relationship("Queue", back_populates="retry_policy")

    def __repr__(self) -> str:
        return f"<RetryPolicy {self.name} ({self.strategy})>"
