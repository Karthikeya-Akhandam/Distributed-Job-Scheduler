"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings sourced from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── General ──────────────────────────────────────────────
    app_name: str = "Distributed Job Scheduler"
    app_env: str = "development"
    debug: bool = True

    # ── PostgreSQL ───────────────────────────────────────────
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "job_scheduler"
    postgres_user: str = "scheduler_user"
    postgres_password: str = "scheduler_secret_password"

    @property
    def database_url(self) -> str:
        """Construct async database URL for SQLAlchemy."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        """Construct sync database URL for Alembic migrations."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ── Redis ────────────────────────────────────────────────
    redis_host: str = "localhost"
    redis_port: int = 6379

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    # ── Backend Server ───────────────────────────────────────
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    # ── JWT ──────────────────────────────────────────────────
    jwt_secret_key: str = "your-super-secret-jwt-key-change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # ── CORS ─────────────────────────────────────────────────
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    # ── AI ───────────────────────────────────────────────────
    ai_provider: str = "mock"  # "gemini" or "mock"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
