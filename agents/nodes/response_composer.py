"""Composable response-composer pipeline node."""
from __future__ import annotations

import json
from typing import Any, Dict

from agents.core.graph_executor import AgentNodeExecutionContext, AgentPipelineNodeResult
from agents.core.pipeline import AgentPipelineNodePlan


def _build_prompt_addition(summary: Dict[str, Any]) -> str:
    compact = json.dumps(summary, ensure_ascii=False)
    return (
        "Internal response-composer node observations:\n"
        f"{compact}\n"
        "Use the accumulated node observations to build one coherent final answer. Prefer the strongest observed "
        "evidence, keep conflicts explicit, and do not imply node actions that never ran."
    )


async def run_response_composer_node(
    context: AgentNodeExecutionContext,
    plan: AgentPipelineNodePlan,
) -> AgentPipelineNodeResult:
    observed_nodes = {
        key: value
        for key, value in context.observations.items()
        if key != "_node_instructions"
    }
    summary_payload = {
        "observed_nodes": sorted(observed_nodes.keys()),
        "degraded_nodes": sorted(
            key for key, value in observed_nodes.items()
            if isinstance(value, dict) and value.get("status") in {"degraded", "failed"}
        ),
        "node_count": len(observed_nodes),
    }
    return AgentPipelineNodeResult(
        status="completed",
        summary="Response composer node summarized the pipeline observations for the final answer.",
        metadata=summary_payload,
        system_prompt_addition=_build_prompt_addition(summary_payload),
    )
