"""Database seeding script for populating development environment with demo data."""

import asyncio
import logging
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.config import get_settings
from app.core.security import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("djs.seed")

settings = get_settings()


async def seed_database():
    """Seed the database with organizations, projects, queues, jobs, and workers."""
    logger.info("Initializing database seed process...")
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Clear existing data safely
        await session.execute(text("TRUNCATE users, organizations, queues, jobs CASCADE"))

        # 1. Create Default Admin User
        user_id = uuid.uuid4()
        user_pw_hash = hash_password("admin_password")
        await session.execute(
            text("""
                INSERT INTO users (id, email, password_hash, name, role, is_active, created_at, updated_at)
                VALUES (:id, 'admin@antigravity.io', :pw, 'Default Admin', 'superadmin', true, NOW(), NOW())
            """),
            {"id": user_id, "pw": user_pw_hash}
        )

        # 2. Create Default Organization
        org_id = uuid.uuid4()
        await session.execute(
            text("""
                INSERT INTO organizations (id, name, slug, created_at)
                VALUES (:id, 'Antigravity Workspace', 'antigravity-workspace', NOW())
            """),
            {"id": org_id}
        )

        # 3. Bind User as Org Owner
        await session.execute(
            text("""
                INSERT INTO org_members (id, user_id, org_id, role, joined_at)
                VALUES (:id, :user_id, :org_id, 'owner', NOW())
            """),
            {"id": uuid.uuid4(), "user_id": user_id, "org_id": org_id}
        )

        # 4. Create Project
        project_id = uuid.uuid4()
        await session.execute(
            text("""
                INSERT INTO projects (id, org_id, name, slug, description, created_at)
                VALUES (:id, :org_id, 'Production Scheduler', 'production-scheduler', 'Core processing engines', NOW())
            """),
            {"id": project_id, "org_id": org_id}
        )

        # 5. Create Retry Policy
        retry_policy_id = uuid.uuid4()
        await session.execute(
            text("""
                INSERT INTO retry_policies (id, name, strategy, max_retries, initial_delay_ms, backoff_multiplier, max_delay_ms, created_at)
                VALUES (:id, 'Standard Backoff', 'exponential', 3, 1000, 2.0, 300000, NOW())
            """),
            {"id": retry_policy_id}
        )

        # 6. Create Queue
        queue_id = uuid.uuid4()
        await session.execute(
            text("""
                INSERT INTO queues (id, project_id, name, priority, concurrency_limit, retry_policy_id, status, shard_count, created_at)
                VALUES (:id, :project_id, 'high-priority-jobs', 8, 10, :policy_id, 'active', 1, NOW())
            """),
            {"id": queue_id, "project_id": project_id, "policy_id": retry_policy_id}
        )

        # 7. Create Demo Jobs
        # Job 1: Completed
        await session.execute(
            text("""
                INSERT INTO jobs (id, queue_id, name, type, status, priority, payload, attempt_number, max_retries, created_at, updated_at)
                VALUES (:id, :queue_id, 'Sync User Details', 'immediate', 'completed', 5, '{"userId": 102}', 1, 3, NOW(), NOW())
            """),
            {"id": uuid.uuid4(), "queue_id": queue_id}
        )

        # Job 2: Queued
        await session.execute(
            text("""
                INSERT INTO jobs (id, queue_id, name, type, status, priority, payload, attempt_number, max_retries, created_at, updated_at)
                VALUES (:id, :queue_id, 'Generate Monthly Invoice', 'delayed', 'queued', 8, '{"invoiceId": 4501}', 0, 3, NOW(), NOW())
            """),
            {"id": uuid.uuid4(), "queue_id": queue_id}
        )

        await session.commit()
        logger.info("Database seeding completed successfully.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_database())
