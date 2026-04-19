"""Composable execution-snapshot pipeline node."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from agents.core.graph_executor import AgentNodeExecutionContext, AgentPipelineNodeResult
from agents.core.pipeline import AgentPipelineNodePlan, SPECIALIST_TARGET_EXECUTION, resolve_specialist_target


async def _call_required_tool(
    context: AgentNodeExecutionContext,
    tool_name: str,
    arguments: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any], Optional[str]]:
    if context.call_tool is None:
        return False, {}, "No tool caller available for execution snapshot node."

    result = await context.call_tool(tool_name, arguments)
    if getattr(result, "success", False):
        return True, getattr(result, "data", {}) or {}, None
    return False, {}, getattr(result, "error", None) or "Unknown tool failure"


def _build_prompt_addition(summary: Dict[str, Any]) -> str:
    compact = json.dumps(summary, ensure_ascii=False)
    return (
        "Internal execution-snapshot node observations:\n"
        f"{compact}\n"
        "Treat these observations as trusted backend-generated execution-readiness context."
    )


async def run_execution_snapshot_node(
    context: AgentNodeExecutionContext,
    plan: AgentPipelineNodePlan,
) -> AgentPipelineNodeResult:
    if resolve_specialist_target(context.intent_context) != SPECIALIST_TARGET_EXECUTION:
        return AgentPipelineNodeResult(
            status="skipped",
            summary="Execution snapshot node skipped because the request is not execution-oriented.",
        )

    errors: List[str] = []
    sections: Dict[str, Any] = {
        "backpack_execution": dict(getattr(context.agent, "last_backpack_execution", {}) or {}),
        "drift_execution": dict(getattr(context.agent, "last_drift_execution", {}) or {}),
    }
    loop_actions: List[str] = []

    for tool_name in ("backpack_get_open_orders", "drift_get_open_orders"):
        ok, payload, error = await _call_required_tool(context, tool_name, {})
        loop_actions.append(tool_name)
        if ok:
            sections[tool_name] = payload
        elif error:
            errors.append(f"{tool_name}: {error}")

    summary_payload = {
        "execution_sections": sections,
        "loop_trace": [
            {
                "phase": "Reason-Act-Critique-Observe",
                "reason": "Gather execution readiness and open-order state before the final response.",
                "actions": loop_actions,
                "critique": "The node stayed read-only and focused on readiness plus current order state.",
                "observe": {
                    "successful_sections": sorted(k for k in sections.keys() if k.endswith("open_orders")),
                    "error_count": len(errors),
                },
            }
        ],
        "errors": errors,
    }

    status = "completed" if len(sections) > 2 and not errors else "degraded"
    if len(sections) == 2 and errors:
        status = "degraded"

    return AgentPipelineNodeResult(
        status=status,
        summary=(
            "Execution snapshot node gathered readiness state and open orders."
            if status == "completed"
            else "Execution snapshot node gathered partial execution context."
        ),
        metadata=summary_payload,
        system_prompt_addition=_build_prompt_addition(summary_payload),
    )
