"""Retry delay calculation utilities for different backoff strategies."""


def calculate_retry_delay(
    strategy: str,
    attempt: int,
    initial_delay_ms: int,
    backoff_multiplier: float = 2.0,
    max_delay_ms: int = 300000,
) -> int:
    """Calculate the delay before the next retry attempt.

    Args:
        strategy: One of "fixed", "linear", or "exponential".
        attempt: Current attempt number (1-indexed).
        initial_delay_ms: Base delay in milliseconds.
        backoff_multiplier: Multiplier for exponential backoff.
        max_delay_ms: Maximum delay cap in milliseconds.

    Returns:
        Delay in milliseconds before the next retry.
    """
    if attempt < 1:
        return initial_delay_ms

    if strategy == "fixed":
        delay = initial_delay_ms
    elif strategy == "linear":
        delay = initial_delay_ms * attempt
    elif strategy == "exponential":
        delay = initial_delay_ms * (backoff_multiplier ** (attempt - 1))
    else:
        # Fallback to fixed delay for unknown strategies
        delay = initial_delay_ms

    return min(int(delay), max_delay_ms)
