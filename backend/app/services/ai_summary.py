"""AI-generated failure summaries for DLQ entries.

Supports configurable providers:
- "gemini": Uses Google Gemini API for intelligent failure analysis
- "mock": Template-based summaries (no API key required)
"""

import json
import logging
from typing import Any

from app.config import get_settings

logger = logging.getLogger("djs.ai_summary")
settings = get_settings()

SUMMARY_PROMPT = """Analyze this job failure and provide a concise, actionable summary.

Job Name: {job_name}
Total Attempts: {total_attempts}
Last Error: {error_message}

Execution History:
{execution_history}

Provide:
1. Root cause analysis (1-2 sentences)
2. Likely fix (1-2 sentences)
3. Severity assessment (LOW/MEDIUM/HIGH/CRITICAL)

Format as a brief paragraph, no bullet points or headers."""


async def generate_failure_summary(
    job_name: str,
    error_message: str,
    total_attempts: int,
    execution_history: list[dict[str, Any]],
) -> str:
    """Generate an AI-powered failure analysis summary.

    Args:
        job_name: Name of the failed job.
        error_message: The final error message.
        total_attempts: Number of execution attempts.
        execution_history: List of execution attempt details.

    Returns:
        Human-readable failure analysis string.
    """
    if settings.ai_provider == "gemini":
        return await _generate_gemini_summary(
            job_name, error_message, total_attempts, execution_history
        )
    else:
        return _generate_mock_summary(
            job_name, error_message, total_attempts, execution_history
        )


async def _generate_gemini_summary(
    job_name: str,
    error_message: str,
    total_attempts: int,
    execution_history: list[dict[str, Any]],
) -> str:
    """Generate summary using Google Gemini API."""
    try:
        from google import genai

        client = genai.Client(api_key=settings.gemini_api_key)

        history_text = "\n".join(
            f"  Attempt {e.get('attempt', '?')}: {e.get('status', 'unknown')} - {e.get('error', 'N/A')}"
            for e in execution_history
        )

        prompt = SUMMARY_PROMPT.format(
            job_name=job_name,
            total_attempts=total_attempts,
            error_message=error_message,
            execution_history=history_text or "No execution history available",
        )

        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
        )

        return response.text.strip()

    except Exception as exc:
        logger.exception("Gemini API call failed, falling back to mock summary")
        return _generate_mock_summary(
            job_name, error_message, total_attempts, execution_history
        )


def _generate_mock_summary(
    job_name: str,
    error_message: str,
    total_attempts: int,
    execution_history: list[dict[str, Any]],
) -> str:
    """Generate a template-based summary (no API key required)."""
    error_lower = error_message.lower()

    # Pattern matching for common errors
    if "timeout" in error_lower or "timed out" in error_lower:
        category = "connectivity/timeout"
        fix = "Check network connectivity and increase timeout thresholds"
        severity = "MEDIUM"
    elif "rate limit" in error_lower:
        category = "rate limiting"
        fix = "Implement request throttling or increase rate limit quotas"
        severity = "LOW"
    elif "memory" in error_lower or "oom" in error_lower:
        category = "resource exhaustion"
        fix = "Increase memory allocation or optimize job payload processing"
        severity = "HIGH"
    elif "deadlock" in error_lower:
        category = "database concurrency"
        fix = "Review transaction isolation levels and query ordering"
        severity = "HIGH"
    elif "503" in error_lower or "unavailable" in error_lower:
        category = "upstream service failure"
        fix = "Verify upstream service health; consider circuit breaker pattern"
        severity = "MEDIUM"
    elif "500" in error_lower:
        category = "internal server error"
        fix = "Review application logs for stack trace details"
        severity = "HIGH"
    else:
        category = "application error"
        fix = "Review the error message and execution logs for detailed debugging"
        severity = "MEDIUM"

    return (
        f"[{severity}] Job '{job_name}' failed after {total_attempts} attempts due to "
        f"{category}. Error: \"{error_message}\". "
        f"Recommended action: {fix}. "
        f"The repeated failure pattern across {total_attempts} attempts suggests "
        f"{'a transient issue that may resolve with longer retry intervals' if total_attempts <= 3 else 'a persistent issue requiring manual investigation'}."
    )
