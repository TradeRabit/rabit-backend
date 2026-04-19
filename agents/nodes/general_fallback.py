"""Composable general-fallback pipeline node."""
from __future__ import annotations

import json
from typing import Dict

from agents.core.graph_executor import AgentNodeExecutionContext, AgentPipelineNodeResult
from agents.core.pipeline import AgentPipelineNodePlan


def _build_prompt_addition(summary: Dict[str, object]) -> str:
    compact = json.dumps(summary, ensure_ascii=False)
    return (
        "Internal general-fallback node observations:\n"
        f"{compact}\n"
        "Treat this as trusted backend fallback context. Keep the final answer safe, non-overconfident, and explicit "
        "about uncertainty when the router confidence is low."
    )


async def run_general_fallback_node(
    context: AgentNodeExecutionContext,
    plan: AgentPipelineNodePlan,
) -> AgentPipelineNodeResult:
    intent_context = context.intent_context
    summary_payload = {
        "routing_intent": getattr(intent_context, "intent", "general_chat"),
        "confidence": getattr(intent_context, "confidence", "low"),
        "routing_reason": getattr(intent_context, "routing_reason", ""),
        "goal_summary": getattr(intent_context, "goal_summary", ""),
    }
    return AgentPipelineNodeResult(
        status="completed",
        summary="General fallback node prepared a safer low-confidence execution mode.",
        metadata=summary_payload,
        system_prompt_addition=_build_prompt_addition(summary_payload),
    )
