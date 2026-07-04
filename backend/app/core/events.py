"""Redis Pub/Sub event system for real-time notifications.

Events are published when job/worker/queue state changes occur.
The WebSocket server and workers subscribe to relevant channels.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as aioredis
from fastapi import Request

logger = logging.getLogger("djs.events")

# Event channel names
CHANNELS = {
    "job_created": "events:job:created",
    "job_status_changed": "events:job:status_changed",
    "job_completed": "events:job:completed",
    "job_failed": "events:job:failed",
    "worker_online": "events:worker:online",
    "worker_offline": "events:worker:offline",
    "worker_heartbeat": "events:worker:heartbeat",
    "queue_paused": "events:queue:paused",
    "queue_resumed": "events:queue:resumed",
    "dlq_entry": "events:dlq:entry",
}


async def publish_event(
    redis: aioredis.Redis,
    event_type: str,
    data: dict[str, Any],
) -> None:
    """Publish an event to a Redis Pub/Sub channel.

    Args:
        redis: Redis client instance.
        event_type: Key from CHANNELS dict.
        data: Event payload.
    """
    channel = CHANNELS.get(event_type)
    if not channel:
        logger.warning("Unknown event type: %s", event_type)
        return

    message = json.dumps({
        "type": event_type,
        "data": _serialize(data),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    try:
        await redis.publish(channel, message)
        logger.debug("Published %s event to %s", event_type, channel)
    except Exception:
        logger.exception("Failed to publish event %s", event_type)


def _serialize(obj: Any) -> Any:
    """Recursively serialize objects for JSON."""
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialize(v) for v in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, "__str__") and not isinstance(obj, (str, int, float, bool)):
        return str(obj)
    return obj


def get_redis(request: Request) -> aioredis.Redis:
    """FastAPI dependency to get the Redis client from app state."""
    return request.app.state.redis
