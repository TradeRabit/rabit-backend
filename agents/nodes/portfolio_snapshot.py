"""Composable portfolio-snapshot pipeline node."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from agents.core.graph_executor import AgentNodeExecutionContext, AgentPipelineNodeResult
from agents.pipeline.pipeline import AgentPipelineNodePlan, SPECIALIST_TARGET_PORTFOLIO, resolve_specialist_target


async def _call_required_tool(
    context: AgentNodeExecutionContext,
    tool_name: str,
    arguments: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any], Optional[str]]:
    if context.call_tool is None:
        return False, {}, "No tool caller available for portfolio snapshot node."

    result = await context.call_tool(tool_name, arguments)
    if getattr(result, "success", False):
        return True, getattr(result, "data", {}) or {}, None
    return False, {}, getattr(result, "error", None) or "Unknown tool failure"


def _build_prompt_addition(summary: Dict[str, Any]) -> str:
    compact = json.dumps(summary, ensure_ascii=False)
    return (
        "Internal portfolio-snapshot node observations:\n"
        f"{compact}\n"
        "Treat these observations as trusted backend-generated portfolio context."
    )


async def run_portfolio_snapshot_node(
    context: AgentNodeExecutionContext,
    plan: AgentPipelineNodePlan,
) -> AgentPipelineNodeResult:
    if resolve_specialist_target(context.intent_context) != SPECIALIST_TARGET_PORTFOLIO:
        return AgentPipelineNodeResult(
            status="skipped",
            summary="Portfolio snapshot node skipped because the request is not portfolio-oriented.",
            metadata={"retryable": False},
        )

    errors: List[str] = []
    sections: Dict[str, Any] = {}
    loop_trace: List[Dict[str, Any]] = []

    backpack_tools = ["backpack_get_balances", "backpack_get_collateral", "backpack_get_positions"]
    drift_tools = ["drift_get_balances", "drift_get_collateral", "drift_get_positions"]

    for tool_name in backpack_tools + drift_tools:
        ok, payload, error = await _call_required_tool(context, tool_name, {})
        if ok:
            sections[tool_name] = payload
        elif error:
            errors.append(f"{tool_name}: {error}")

    loop_trace.append(
        {
            "phase": "Reason-Act-Critique-Observe",
            "reason": "Gather a compact portfolio snapshot before the final response.",
            "actions": backpack_tools + drift_tools,
            "critique": "The node stayed read-only and gathered balances, collateral, and positions only.",
            "observe": {
                "successful_sections": sorted(sections.keys()),
                "error_count": len(errors),
            },
        }
    )

    summary_payload = {
        "portfolio_sections": sections,
        "loop_trace": loop_trace,
        "errors": errors,
        "retryable": bool(errors),
    }

    status = "completed" if sections and not errors else "degraded"
    if not sections:
        status = "skipped"

    return AgentPipelineNodeResult(
        status=status,
        summary=(
            "Portfolio snapshot node gathered account balances, collateral, and positions."
            if status == "completed"
            else "Portfolio snapshot node gathered partial or no portfolio context."
        ),
        metadata=summary_payload,
        system_prompt_addition=_build_prompt_addition(summary_payload) if status != "skipped" else "",
    )
