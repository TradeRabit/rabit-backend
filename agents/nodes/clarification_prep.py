"""Composable clarification-prep pipeline node."""
from __future__ import annotations

import json
from typing import Dict

from agents.core.graph_executor import AgentNodeExecutionContext, AgentPipelineNodeResult
from agents.pipeline.pipeline import AgentPipelineNodePlan


def _build_prompt_addition(summary: Dict[str, object]) -> str:
    compact = json.dumps(summary, ensure_ascii=False)
    return (
        "Internal clarification-prep node observations:\n"
        f"{compact}\n"
        "Treat this as trusted routing context. Ask only the minimum clarification needed to unblock the task. "
        "If hint options are available, prefer a structured hint over an open-ended question."
    )


async def run_clarification_prep_node(
    context: AgentNodeExecutionContext,
    plan: AgentPipelineNodePlan,
) -> AgentPipelineNodeResult:
    intent_context = context.intent_context
    summary_payload = {
        "should_clarify": True,
        "clarification_reason": getattr(intent_context, "clarification_reason", ""),
        "suggested_hint_title": getattr(intent_context, "suggested_hint_title", ""),
        "suggested_hint_options": getattr(intent_context, "suggested_hint_options", []),
        "retryable": False,
    }
    return AgentPipelineNodeResult(
        status="completed",
        summary="Clarification prep node gathered the minimum structured clarification context.",
        metadata=summary_payload,
        system_prompt_addition=_build_prompt_addition(summary_payload),
    )
