import asyncio

from agents.tools.core.runtime_context import (
    reset_current_event_emitter,
    set_current_event_emitter,
)
from agents.tools.tradingview.screenshot import tv_capture_screenshot
from agents.tools.ui.ui_stream_tools import show_hint, show_plan, show_thinking_summary


def test_ui_stream_tools_emit_structured_payloads():
    events = []

    async def emitter(event_name, payload):
        events.append((event_name, payload))

    token = set_current_event_emitter(emitter)
    try:
        thinking = asyncio.run(show_thinking_summary("I am checking price and risk first"))
        plan = asyncio.run(
            show_plan(
                "Trade Plan",
                "running",
                '[{"id":1,"label":"Check price","status":"done"},{"id":2,"label":"Set order","status":"pending"}]',
            )
        )
        hint = asyncio.run(
            show_hint(
                "Choose strategy",
                '[{"id":"opt1","text":"Scalp"},{"id":"opt2","text":"Swing"}]',
            )
        )
    finally:
        reset_current_event_emitter(token)

    assert thinking["streamed"] is True
    assert plan["payload"]["type"] == "plan"
    assert hint["payload"]["type"] == "hint"
    assert events[0][0] == "thinking_summary"
    assert events[1][0] == "plan"
    assert events[2][0] == "hint"


def test_ui_stream_tools_validate_json():
    try:
        asyncio.run(show_plan("Bad Plan", "running", '{"oops":true}'))
    except ValueError as exc:
        assert "steps_json must be a JSON array" in str(exc)
    else:
        raise AssertionError("Expected show_plan to reject invalid JSON shape")


def test_tradingview_screenshot_emits_chart_screenshot_event(monkeypatch):
    events = []

    class DummyClient:
        async def send_command(self, command, params):
            assert command == "CAPTURE_SCREENSHOT"
            assert params == {"region": "chart"}
            return {
                "success": True,
                "data": {
                    "screenshot_url": "http://localhost:3001/mock-chart.png",
                },
            }

    async def emitter(event_name, payload):
        events.append((event_name, payload))

    async def fake_download(_url):
        return {
            "content_type": "image/png",
            "data_base64": "aW1hZ2UtYnl0ZXM=",
            "size_bytes": 11,
        }

    monkeypatch.setattr("agents.tools.tradingview.screenshot.get_client", lambda: DummyClient())
    monkeypatch.setattr(
        "agents.tools.tradingview.screenshot._download_screenshot_asset",
        fake_download,
    )

    token = set_current_event_emitter(emitter)
    try:
        result = asyncio.run(tv_capture_screenshot("chart"))
    finally:
        reset_current_event_emitter(token)

    assert result["success"] is True
    assert result["screenshot_url"] == "http://localhost:3001/mock-chart.png"
    assert result["agent_image_available"] is True
    assert result["streamed"] is True
    assert result["data"]["agent_image"]["content_type"] == "image/png"
    assert events == [
        (
            "chart_screenshot",
            {
                "type": "chart_screenshot",
                "region": "chart",
                "screenshot_url": "http://localhost:3001/mock-chart.png",
                "agent_image_available": True,
            },
        )
    ]
