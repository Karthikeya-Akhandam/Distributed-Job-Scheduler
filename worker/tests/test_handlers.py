import pytest
from app.handlers.base import get_handler, SimulatedHandler, HttpWebhookHandler, ScriptHandler

def test_get_handler():
    assert isinstance(get_handler("immediate"), SimulatedHandler)
    assert isinstance(get_handler("delayed"), SimulatedHandler)
    assert isinstance(get_handler("http_webhook"), HttpWebhookHandler)
    assert isinstance(get_handler("script"), ScriptHandler)
    # Default fallback
    assert isinstance(get_handler("unknown_type"), SimulatedHandler)

@pytest.mark.asyncio
async def test_simulated_handler_success():
    handler = SimulatedHandler()
    payload = {"duration_ms": 10, "failure_rate": 0.0}
    result = await handler.execute(payload)
    assert result["status"] == "success"
    assert result["duration_ms"] == 10

@pytest.mark.asyncio
async def test_simulated_handler_failure():
    handler = SimulatedHandler()
    payload = {"duration_ms": 10, "failure_rate": 1.0, "error_message": "Forced failure"}
    with pytest.raises(RuntimeError) as exc_info:
        await handler.execute(payload)
    assert "Forced failure" in str(exc_info.value)
