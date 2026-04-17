import asyncio

from agents.tools.core.runtime_context import (
    reset_current_event_emitter,
    set_current_event_emitter,
)
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
