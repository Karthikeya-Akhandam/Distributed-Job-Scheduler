"""Graceful shutdown coordinator for the worker service.

Handles SIGTERM/SIGINT signals:
1. Stop accepting new jobs (stop polling)
2. Wait for in-flight jobs to finish
3. Mark worker as offline
4. Exit cleanly
"""

import asyncio
import logging
import signal

logger = logging.getLogger("djs.worker.shutdown")


class ShutdownCoordinator:
    """Manages graceful shutdown of the worker process."""

    def __init__(self):
        self._shutdown_event = asyncio.Event()
        self._setup_done = False

    @property
    def should_shutdown(self) -> bool:
        """Check if shutdown has been requested."""
        return self._shutdown_event.is_set()

    def setup_signal_handlers(self, loop: asyncio.AbstractEventLoop) -> None:
        """Register SIGTERM and SIGINT handlers."""
        if self._setup_done:
            return

        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(sig, self._handle_signal, sig)
            except NotImplementedError:
                # Windows doesn't support add_signal_handler for all signals
                signal.signal(sig, lambda s, f: self._handle_signal(s))

        self._setup_done = True
        logger.info("Signal handlers registered (SIGTERM, SIGINT)")

    def _handle_signal(self, sig) -> None:
        """Handle shutdown signal."""
        sig_name = signal.Signals(sig).name if isinstance(sig, int) else str(sig)
        logger.info("Received %s — initiating graceful shutdown", sig_name)
        self._shutdown_event.set()

    async def wait_for_shutdown(self) -> None:
        """Block until a shutdown signal is received."""
        await self._shutdown_event.wait()

    def request_shutdown(self) -> None:
        """Programmatically request shutdown (e.g., from health check failure)."""
        self._shutdown_event.set()
