"""Redis-based distributed rate limiting and distributed locking utilities."""

import logging
import time
import uuid
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger("djs.rate_limit_lock")


# ── Rate Limiter ─────────────────────────────────────────────

class RedisRateLimiter:
    """Token bucket or sliding window rate limiter using Redis."""

    def __init__(self, redis: aioredis.Redis):
        self.redis = redis

    async def is_rate_limited(self, queue_id: str, limit_per_minute: int) -> bool:
        """Check if a queue is currently rate-limited.

        Uses a sliding window counter approach in Redis.
        """
        current_minute = int(time.time() / 60)
        key = f"rate:queue:{queue_id}:{current_minute}"

        # Increment call count for the current minute window
        count = await self.redis.incr(key)
        if count == 1:
            # Set TTL to 2 minutes so key gets cleaned up automatically
            await self.redis.expire(key, 120)

        return count > limit_per_minute


# ── Distributed Lock ─────────────────────────────────────────

class PGAdvisoryLock:
    """Distributed locking using PostgreSQL transaction-level advisory locks."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def acquire_lock(self, key_id: int) -> bool:
        """Acquire a transaction-level advisory lock.

        The lock is automatically released when the transaction commits or rolls back.
        """
        stmt = text("SELECT pg_try_advisory_xact_lock(:key_id)")
        result = await self.db.execute(stmt, {"key_id": key_id})
        acquired = result.scalar() or False
        if acquired:
            logger.debug("Advisory lock acquired for key %d", key_id)
        return acquired
