"""Composable execution-snapshot pipeline node."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from agents.core.graph_executor import AgentNodeExecutionContext, AgentPipelineNodeResult
from agents.pipeline.pipeline import AgentPipelineNodePlan, SPECIALIST_TARGET_EXECUTION, resolve_specialist_target


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
            metadata={"retryable": False},
        )

    errors: List[str] = []
    execution_gate = dict(getattr(context.agent, "last_execution_gate", {}) or {})
    execution_gate_enabled = bool(execution_gate.get("enabled"))
    sections: Dict[str, Any] = {
        "execution_gate": execution_gate,
    }

    summary_payload = {
        "execution_sections": sections,
        "loop_trace": [
            {
                "phase": "Reason-Act-Critique-Observe",
                "reason": "Gather execution readiness before the final response.",
                "actions": ["execution_gate"],
                "critique": "The node stayed read-only and focused on whether live execution is currently allowed.",
                "observe": {
                    "successful_sections": sorted(sections.keys()),
                    "error_count": len(errors),
                    "execution_gate_enabled": execution_gate_enabled,
                },
            }
        ],
        "errors": errors,
        "execution_gate_enabled": execution_gate_enabled,
        "retryable": bool(errors),
    }

    status = "completed" if not errors else "degraded"

    return AgentPipelineNodeResult(
        status=status,
        summary=(
            "Execution snapshot node gathered current live-execution readiness."
            if status == "completed"
            else "Execution snapshot node gathered partial execution context."
        ),
        metadata=summary_payload,
        system_prompt_addition=_build_prompt_addition(summary_payload),
    )
