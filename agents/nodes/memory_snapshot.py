"""Composable memory-snapshot pipeline node."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from agents.core.graph_executor import AgentNodeExecutionContext, AgentPipelineNodeResult
from agents.core.pipeline import AgentPipelineNodePlan, SPECIALIST_TARGET_MEMORY, resolve_specialist_target


async def _call_required_tool(
    context: AgentNodeExecutionContext,
    tool_name: str,
    arguments: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any], Optional[str]]:
    if context.call_tool is None:
        return False, {}, "No tool caller available for memory snapshot node."

    result = await context.call_tool(tool_name, arguments)
    if getattr(result, "success", False):
        return True, getattr(result, "data", {}) or {}, None
    return False, {}, getattr(result, "error", None) or "Unknown tool failure"


def _build_prompt_addition(summary: Dict[str, Any]) -> str:
    compact = json.dumps(summary, ensure_ascii=False)
    return (
        "Internal memory-snapshot node observations:\n"
        f"{compact}\n"
        "Treat these observations as trusted backend-generated memory context."
    )


async def run_memory_snapshot_node(
    context: AgentNodeExecutionContext,
    plan: AgentPipelineNodePlan,
) -> AgentPipelineNodeResult:
    if resolve_specialist_target(context.intent_context) != SPECIALIST_TARGET_MEMORY:
        return AgentPipelineNodeResult(
            status="skipped",
            summary="Memory snapshot node skipped because the request is not memory-oriented.",
        )

    ok, payload, error = await _call_required_tool(
        context,
        "get_user_memory",
        {
            "query": context.user_input,
            "limit": int(plan.config.get("memory_limit", 5) or 5),
        },
    )

    errors = [f"get_user_memory: {error}"] if error else []
    summary_payload = {
        "memory_results": payload if ok else {},
        "loop_trace": [
            {
                "phase": "Reason-Act-Critique-Observe",
                "reason": "Gather relevant user memory before the final response.",
                "actions": ["get_user_memory"],
                "critique": "The node stayed read-only and recalled relevant durable context only.",
                "observe": {
                    "memory_available": ok,
                    "error_count": len(errors),
                },
            }
        ],
        "errors": errors,
    }

    status = "completed" if ok and not errors else "degraded"
    if not ok and not payload:
        status = "degraded"

    return AgentPipelineNodeResult(
        status=status,
        summary=(
            "Memory snapshot node recalled relevant stored memory."
            if status == "completed"
            else "Memory snapshot node returned partial or degraded memory context."
        ),
        metadata=summary_payload,
        system_prompt_addition=_build_prompt_addition(summary_payload),
    )
