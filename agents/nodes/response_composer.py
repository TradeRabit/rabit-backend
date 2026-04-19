"""Composable response-composer pipeline node."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

from agents.core.graph_executor import AgentNodeExecutionContext, AgentPipelineNodeResult
from agents.pipeline.pipeline import AgentPipelineNodePlan


def _build_prompt_addition(summary: Dict[str, Any]) -> str:
    compact = json.dumps(summary, ensure_ascii=False)
    return (
        "Internal response-composer node observations:\n"
        f"{compact}\n"
        "Use the accumulated node observations to build one coherent final answer. Prefer the strongest observed "
        "evidence, keep conflicts explicit, follow the recommended posture, and do not imply node actions that never ran."
    )


def _extract_symbol_and_timeframe(observed_nodes: Dict[str, Any], market_context: Dict[str, Any]) -> Tuple[str | None, str | None]:
    chart = observed_nodes.get("chart_analysis", {}) if isinstance(observed_nodes.get("chart_analysis"), dict) else {}
    market = observed_nodes.get("market_snapshot", {}) if isinstance(observed_nodes.get("market_snapshot"), dict) else {}
    symbol = (
        chart.get("effective_symbol")
        or chart.get("requested_symbol")
        or market.get("resolved_symbol")
        or market_context.get("symbol")
    )
    timeframe = (
        chart.get("effective_timeframe")
        or chart.get("requested_timeframe")
        or market_context.get("timeframe")
    )
    return symbol, timeframe


def _derive_evidence_priority(observed_nodes: Dict[str, Any]) -> Dict[str, List[str]]:
    primary_order = [
        "risk_review",
        "chart_analysis",
        "market_snapshot",
        "execution_snapshot",
        "portfolio_snapshot",
        "research_snapshot",
        "memory_snapshot",
    ]
    completed = [
        name
        for name, value in observed_nodes.items()
        if isinstance(value, dict) and value.get("status") == "completed"
    ]
    degraded = [
        name
        for name, value in observed_nodes.items()
        if isinstance(value, dict) and value.get("status") in {"degraded", "failed"}
    ]
    primary = [name for name in primary_order if name in completed]
    supporting = sorted(name for name in completed if name not in primary)
    return {
        "primary_evidence_nodes": primary,
        "supporting_nodes": supporting,
        "degraded_nodes": sorted(degraded),
    }


def _collect_conflict_flags(observed_nodes: Dict[str, Any]) -> List[Dict[str, str]]:
    conflicts: List[Dict[str, str]] = []
    chart = observed_nodes.get("chart_analysis", {}) if isinstance(observed_nodes.get("chart_analysis"), dict) else {}
    market = observed_nodes.get("market_snapshot", {}) if isinstance(observed_nodes.get("market_snapshot"), dict) else {}
    execution = observed_nodes.get("execution_snapshot", {}) if isinstance(observed_nodes.get("execution_snapshot"), dict) else {}
    risk = observed_nodes.get("risk_review", {}) if isinstance(observed_nodes.get("risk_review"), dict) else {}

    chart_symbol = str(chart.get("effective_symbol") or chart.get("requested_symbol") or "").strip().upper()
    market_symbol = str(market.get("resolved_symbol") or "").strip().upper()
    if chart_symbol and market_symbol and chart_symbol != market_symbol:
        conflicts.append(
            {
                "flag": "symbol_context_mismatch",
                "reason": f"Chart evidence points to {chart_symbol} while market snapshot resolved {market_symbol}.",
                "severity": "high",
            }
        )

    fresh_news_count = int(risk.get("fresh_headline_count") or 0)
    if fresh_news_count > 0 and chart.get("status") == "completed":
        conflicts.append(
            {
                "flag": "fresh_news_fragility",
                "reason": "Fresh asset-specific headlines may destabilize an otherwise technical setup.",
                "severity": "medium",
            }
        )

    if execution.get("status") in {"completed", "degraded"} and execution.get("execution_gate_enabled") is False:
        conflicts.append(
            {
                "flag": "execution_gate_disabled",
                "reason": "The request has execution context, but no live execution path is enabled.",
                "severity": "medium",
            }
        )

    degraded_nodes = [
        name
        for name, value in observed_nodes.items()
        if isinstance(value, dict) and value.get("status") in {"degraded", "failed"}
    ]
    if degraded_nodes:
        conflicts.append(
            {
                "flag": "degraded_upstream_context",
                "reason": f"Some upstream nodes degraded: {', '.join(sorted(degraded_nodes))}.",
                "severity": "high",
            }
        )

    if risk.get("caution_level") == "high":
        conflicts.append(
            {
                "flag": "high_risk_posture",
                "reason": "Risk review marked the setup as high caution.",
                "severity": "high",
            }
        )

    return conflicts


def _derive_recommended_posture(
    *,
    observed_nodes: Dict[str, Any],
    conflict_flags: List[Dict[str, str]],
) -> str:
    if "clarification_prep" in observed_nodes:
        return "clarify"
    if "general_fallback" in observed_nodes:
        return "uncertainty_aware"
    if any(flag.get("severity") == "high" for flag in conflict_flags):
        return "cautious"
    if conflict_flags:
        return "balanced"
    if "risk_review" in observed_nodes:
        return "risk_first"
    return "direct"


async def run_response_composer_node(
    context: AgentNodeExecutionContext,
    plan: AgentPipelineNodePlan,
) -> AgentPipelineNodeResult:
    observed_nodes = {
        key: value
        for key, value in context.observations.items()
        if key != "_node_instructions"
    }
    evidence = _derive_evidence_priority(observed_nodes)
    conflict_flags = _collect_conflict_flags(observed_nodes)
    resolved_symbol, resolved_timeframe = _extract_symbol_and_timeframe(observed_nodes, context.market_context or {})
    recommended_posture = _derive_recommended_posture(
        observed_nodes=observed_nodes,
        conflict_flags=conflict_flags,
    )

    summary_payload = {
        "observed_nodes": sorted(observed_nodes.keys()),
        "node_count": len(observed_nodes),
        "resolved_symbol": resolved_symbol,
        "resolved_timeframe": resolved_timeframe,
        "primary_evidence_nodes": evidence["primary_evidence_nodes"],
        "supporting_nodes": evidence["supporting_nodes"],
        "degraded_nodes": evidence["degraded_nodes"],
        "conflict_flags": conflict_flags,
        "recommended_posture": recommended_posture,
        "artifact_count": len(getattr(context.agent, "last_pipeline_artifacts", []) or []),
        "retryable": False,
    }
    return AgentPipelineNodeResult(
        status="completed",
        summary="Response composer node synthesized evidence, conflicts, and answer posture for the final answer.",
        metadata=summary_payload,
        system_prompt_addition=_build_prompt_addition(summary_payload),
    )
