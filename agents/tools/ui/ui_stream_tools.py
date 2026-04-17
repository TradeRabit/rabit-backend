"""Agent tools for frontend UI events over streaming chat."""
import json
from typing import Any, Dict, List

from agents.tools.core.runtime_context import get_current_event_emitter

PLAN_STATUSES = {"running", "completed", "failed"}
PLAN_STEP_STATUSES = {"done", "processing", "pending", "failed"}


def _parse_json_list(raw: str, field_name: str) -> List[Dict[str, Any]]:
    """Parse a JSON array payload and validate basic shape."""
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field_name} must be valid JSON: {exc.msg}") from exc

    if not isinstance(parsed, list):
        raise ValueError(f"{field_name} must be a JSON array")

    normalized: List[Dict[str, Any]] = []
    for index, item in enumerate(parsed):
        if not isinstance(item, dict):
            raise ValueError(f"{field_name}[{index}] must be an object")
        normalized.append(item)
    return normalized


async def _emit(event_name: str, payload: Dict[str, Any]) -> bool:
    """Emit an event to the current streaming consumer if available."""
    emitter = get_current_event_emitter()
    if emitter is None:
        return False

    await emitter(event_name, payload)
    return True


async def show_thinking_summary(summary: str) -> Dict[str, Any]:
    """Emit a concise thinking summary event for the frontend."""
    summary = (summary or "").strip()
    if not summary:
        raise ValueError("summary is required")

    payload = {
        "type": "thinking_summary",
        "summary": summary,
    }
    streamed = await _emit("thinking_summary", payload)
    return {
        "success": True,
        "streamed": streamed,
        "payload": payload,
    }


async def show_plan(name: str, status: str, steps_json: str) -> Dict[str, Any]:
    """Emit a structured plan event for the frontend."""
    status = (status or "").strip().lower()
    if status not in PLAN_STATUSES:
        raise ValueError(
            f"status must be one of: {', '.join(sorted(PLAN_STATUSES))}"
        )

    steps = _parse_json_list(steps_json, "steps_json")
    normalized_steps: List[Dict[str, Any]] = []
    for index, step in enumerate(steps):
        step_status = str(step.get("status", "")).strip().lower()
        if step_status not in PLAN_STEP_STATUSES:
            raise ValueError(
                f"steps_json[{index}].status must be one of: "
                f"{', '.join(sorted(PLAN_STEP_STATUSES))}"
            )

        label = str(step.get("label", "")).strip()
        if not label:
            raise ValueError(f"steps_json[{index}].label is required")

        normalized_steps.append(
            {
                "id": step.get("id", index + 1),
                "label": label,
                "status": step_status,
            }
        )

    payload = {
        "type": "plan",
        "name": name,
        "status": status,
        "steps": normalized_steps,
    }
    streamed = await _emit("plan", payload)
    return {
        "success": True,
        "streamed": streamed,
        "payload": payload,
    }


async def show_hint(title: str, options_json: str) -> Dict[str, Any]:
    """Emit a HITL hint event for the frontend."""
    title = (title or "").strip()
    if not title:
        raise ValueError("title is required")

    options = _parse_json_list(options_json, "options_json")
    normalized_options: List[Dict[str, Any]] = []
    for index, option in enumerate(options):
        option_id = str(option.get("id", "")).strip()
        option_text = str(option.get("text", "")).strip()
        if not option_id:
            raise ValueError(f"options_json[{index}].id is required")
        if not option_text:
            raise ValueError(f"options_json[{index}].text is required")
        normalized_options.append({"id": option_id, "text": option_text})

    payload = {
        "type": "hint",
        "title": title,
        "options": normalized_options,
    }
    streamed = await _emit("hint", payload)
    return {
        "success": True,
        "streamed": streamed,
        "payload": payload,
    }
