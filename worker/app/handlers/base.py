"""Base handler and simulated job execution handlers.

Since this is a scheduler platform (not executing user code), handlers
simulate work with configurable delays and random success/failure rates.
"""

import asyncio
import logging
import random
from abc import ABC, abstractmethod

logger = logging.getLogger("djs.worker.handlers")


class BaseHandler(ABC):
    """Abstract base class for job execution handlers."""

    @abstractmethod
    async def execute(self, payload: dict | None) -> dict:
        """Execute the job with the given payload.

        Args:
            payload: Job payload data.

        Returns:
            Result dictionary.

        Raises:
            Exception: If the job fails.
        """
        ...


class SimulatedHandler(BaseHandler):
    """Simulates job execution with configurable behavior.

    Payload options:
        - duration_ms: How long to simulate work (default: 500-3000ms random)
        - failure_rate: Probability of failure (0.0-1.0, default: 0.15)
        - error_message: Custom error message on failure
    """

    async def execute(self, payload: dict | None) -> dict:
        payload = payload or {}

        # Determine execution duration
        duration_ms = payload.get("duration_ms", random.randint(500, 3000))
        failure_rate = payload.get("failure_rate", 0.15)

        # Simulate work
        logger.debug("Simulating work for %dms", duration_ms)
        await asyncio.sleep(duration_ms / 1000.0)

        # Random failure based on configured rate
        if random.random() < failure_rate:
            error_msg = payload.get(
                "error_message",
                random.choice([
                    "Connection timeout to external service",
                    "Resource temporarily unavailable",
                    "Rate limit exceeded",
                    "Internal processing error",
                    "Upstream service returned 503",
                    "Memory allocation failed",
                    "Deadlock detected in transaction",
                ]),
            )
            raise RuntimeError(error_msg)

        return {
            "status": "success",
            "duration_ms": duration_ms,
            "processed_at": asyncio.get_event_loop().time(),
            "result_data": payload.get("result_data", {"message": "Job completed successfully"}),
        }


class HttpWebhookHandler(BaseHandler):
    """Simulates an HTTP webhook execution."""

    async def execute(self, payload: dict | None) -> dict:
        payload = payload or {}
        url = payload.get("url", "https://example.com/webhook")
        method = payload.get("method", "POST")

        # Simulate HTTP call
        await asyncio.sleep(random.uniform(0.2, 1.5))

        if random.random() < 0.1:
            raise RuntimeError(f"HTTP {method} to {url} failed with status 500")

        return {
            "status": "success",
            "url": url,
            "method": method,
            "response_code": 200,
        }


class ScriptHandler(BaseHandler):
    """Simulates a script/command execution."""

    async def execute(self, payload: dict | None) -> dict:
        payload = payload or {}
        script = payload.get("script", "echo 'hello world'")

        # Simulate script execution
        await asyncio.sleep(random.uniform(1.0, 5.0))

        if random.random() < 0.1:
            raise RuntimeError(f"Script '{script}' exited with code 1")

        return {
            "status": "success",
            "script": script,
            "exit_code": 0,
            "stdout": "Execution completed",
        }


def get_handler(job_type: str) -> BaseHandler:
    """Factory: return the appropriate handler for a job type."""
    handlers = {
        "immediate": SimulatedHandler(),
        "delayed": SimulatedHandler(),
        "scheduled": SimulatedHandler(),
        "recurring": SimulatedHandler(),
        "batch": SimulatedHandler(),
        "http_webhook": HttpWebhookHandler(),
        "script": ScriptHandler(),
    }
    return handlers.get(job_type, SimulatedHandler())
