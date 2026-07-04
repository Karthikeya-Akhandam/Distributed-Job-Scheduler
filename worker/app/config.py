"""Worker service configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    """Worker-specific settings sourced from environment."""

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ─────────────────────────────────────────────
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "job_scheduler"
    postgres_user: str = "scheduler_user"
    postgres_password: str = "scheduler_secret_password"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ── Redis ────────────────────────────────────────────────
    redis_host: str = "localhost"
    redis_port: int = 6379

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    # ── Worker ───────────────────────────────────────────────
    worker_id: str = "worker-1"
    worker_max_concurrency: int = 10
    worker_poll_interval_seconds: float = 2.0
    worker_heartbeat_interval_seconds: float = 15.0


@lru_cache
def get_worker_settings() -> WorkerSettings:
    return WorkerSettings()
