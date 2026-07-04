"""WebSocket endpoint for live updates.

Subscribes to Redis Pub/Sub channels and forwards events to connected
dashboard clients. Supports JWT authentication via query parameter.
"""

import asyncio
import json
import logging

import redis.asyncio as aioredis
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.events import CHANNELS
from app.core.security import decode_token
from app.config import get_settings

logger = logging.getLogger("djs.websocket")
settings = get_settings()

router = APIRouter()


@router.websocket("/ws/events")
async def websocket_events(
    websocket: WebSocket,
    token: str = Query(default=""),
):
    """WebSocket endpoint that streams real-time events to dashboard clients.

    Authentication is done via JWT token passed as a query parameter.
    The client receives events for job status changes, worker updates,
    queue state changes, and DLQ entries.
    """
    # Authenticate via JWT query param
    if token:
        payload = decode_token(token)
        if not payload:
            await websocket.close(code=4001, reason="Invalid token")
            return
    else:
        # Allow unauthenticated connections in development
        if settings.app_env != "development":
            await websocket.close(code=4001, reason="Authentication required")
            return

    await websocket.accept()
    logger.info("WebSocket client connected")

    # Subscribe to all event channels
    redis: aioredis.Redis = websocket.app.state.redis
    pubsub = redis.pubsub()

    try:
        await pubsub.subscribe(*CHANNELS.values())

        # Forward events to the WebSocket client
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=1.0
            )

            if message and message["type"] == "message":
                try:
                    data = message["data"]
                    if isinstance(data, bytes):
                        data = data.decode("utf-8")
                    await websocket.send_text(data)
                except WebSocketDisconnect:
                    break
                except Exception:
                    logger.exception("Error forwarding message to WebSocket")

            # Small sleep to prevent busy-waiting
            await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception:
        logger.exception("WebSocket error")
    finally:
        await pubsub.unsubscribe(*CHANNELS.values())
        await pubsub.close()
