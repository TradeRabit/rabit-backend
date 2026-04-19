"""Composable risk-review pipeline node."""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Tuple

from agents.core.graph_executor import AgentNodeExecutionContext, AgentPipelineNodeResult
from agents.pipeline.pipeline import AgentPipelineNodePlan


def _build_prompt_addition(summary: Dict[str, Any]) -> str:
    compact = json.dumps(summary, ensure_ascii=False)
    return (
        "Internal risk-review node observations:\n"
        f"{compact}\n"
        "Treat these observations as trusted backend-generated risk context. "
        "Emphasize downside, invalidation, fragility, and caution flags without inventing unsupported controls."
    )


def _extract_numeric_rsi(values: Dict[str, Any]) -> float | None:
    for key, value in values.items():
        if "rsi" not in str(key).lower():
            continue
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, dict):
            for nested in value.values():
                if isinstance(nested, (int, float)):
                    return float(nested)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                continue
    return None


def _extract_symbol_and_timeframe(observations: Dict[str, Any], market_context: Dict[str, Any]) -> Tuple[str | None, str | None]:
    chart = observations.get("chart_analysis", {}) if isinstance(observations.get("chart_analysis"), dict) else {}
    market = observations.get("market_snapshot", {}) if isinstance(observations.get("market_snapshot"), dict) else {}
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


def _collect_degraded_nodes(observations: Dict[str, Any]) -> List[str]:
    degraded: List[str] = []
    for key, value in observations.items():
        if key == "_node_instructions" or not isinstance(value, dict):
            continue
        if value.get("status") in {"degraded", "failed"}:
            degraded.append(key)
    return sorted(degraded)


def _extract_invalidation_markers(chart: Dict[str, Any], user_input: str) -> Tuple[bool, List[str]]:
    labels: List[str] = []
    for section_name in ("applied_actions", "requested_actions"):
        raw = chart.get(section_name, [])
        if not isinstance(raw, list):
            continue
        for item in raw:
            if not isinstance(item, dict):
                continue
            text = str(item.get("text") or item.get("action") or "").strip()
            if text:
                labels.append(text)

    lowered_labels = [label.lower() for label in labels]
    explicit = any(
        keyword in label
        for label in lowered_labels
        for keyword in ("stop", "invalidation", "validation")
    )
    if explicit:
        return True, labels

    lowered_input = (user_input or "").lower()
    explicit = bool(re.search(r"\b(stop(?: loss)?|invalidation|validation)\b", lowered_input))
    return explicit, labels


def _derive_risk_flags(
    *,
    user_input: str,
    observations: Dict[str, Any],
    market_context: Dict[str, Any],
) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
    chart = observations.get("chart_analysis", {}) if isinstance(observations.get("chart_analysis"), dict) else {}
    market = observations.get("market_snapshot", {}) if isinstance(observations.get("market_snapshot"), dict) else {}
    execution = observations.get("execution_snapshot", {}) if isinstance(observations.get("execution_snapshot"), dict) else {}

    flags: List[Dict[str, str]] = []
    degraded_nodes = _collect_degraded_nodes(observations)
    if degraded_nodes:
        flags.append(
            {
                "flag": "degraded_upstream_context",
                "severity": "high",
                "reason": f"Some upstream nodes degraded: {', '.join(degraded_nodes)}.",
            }
        )

    explicit_invalidation, invalidation_labels = _extract_invalidation_markers(chart, user_input)
    if not explicit_invalidation:
        flags.append(
            {
                "flag": "no_explicit_invalidation_observed",
                "severity": "high",
                "reason": "No explicit stop, invalidation, or validation marker was observed in the current setup context.",
            }
        )

    if chart.get("symbol_change_blocked"):
        flags.append(
            {
                "flag": "symbol_change_blocked",
                "severity": "medium",
                "reason": "The chart request tried to move outside a locked asset scope.",
            }
        )

    unmet_requirements = chart.get("unmet_requirements", [])
    if isinstance(unmet_requirements, list) and unmet_requirements:
        flags.append(
            {
                "flag": "incomplete_chart_request",
                "severity": "medium",
                "reason": "The chart workflow was not fully concrete enough to satisfy every requested mutation.",
            }
        )

    news_items = market.get("news_headlines", [])
    if isinstance(news_items, list) and any(isinstance(item, dict) and item.get("is_new") for item in news_items):
        flags.append(
            {
                "flag": "fresh_news_present",
                "severity": "medium",
                "reason": "Recent fresh headlines are present, so setup conditions may be more unstable or event-sensitive.",
            }
        )

    indicator_values = chart.get("indicator_values", {})
    rsi_value = _extract_numeric_rsi(indicator_values if isinstance(indicator_values, dict) else {})
    if rsi_value is not None and rsi_value >= 70:
        flags.append(
            {
                "flag": "rsi_overbought",
                "severity": "medium",
                "reason": f"Observed RSI is elevated at {rsi_value:.2f}.",
            }
        )
    elif rsi_value is not None and rsi_value <= 30:
        flags.append(
            {
                "flag": "rsi_oversold",
                "severity": "medium",
                "reason": f"Observed RSI is depressed at {rsi_value:.2f}.",
            }
        )

    execution_sections = execution.get("execution_sections", {})
    if isinstance(execution_sections, dict):
        backpack_enabled = bool((execution_sections.get("backpack_execution") or {}).get("enabled"))
        drift_enabled = bool((execution_sections.get("drift_execution") or {}).get("enabled"))
        if execution_sections and not (backpack_enabled or drift_enabled):
            flags.append(
                {
                    "flag": "execution_not_enabled",
                    "severity": "low",
                    "reason": "Execution context is present, but no live execution path is enabled.",
                }
            )

    severity_score = 0
    for flag in flags:
        severity_score += {"low": 1, "medium": 2, "high": 3}.get(flag["severity"], 1)
    caution_level = "low"
    if severity_score >= 5:
        caution_level = "high"
    elif severity_score >= 2:
        caution_level = "medium"

    invalidation_quality = "missing"
    if explicit_invalidation:
        invalidation_quality = "explicit"
    elif invalidation_labels:
        invalidation_quality = "implicit"

    indicator_signal_count = 1 if rsi_value is not None else 0
    market_signal_count = 1 if market.get("price_snapshot") else 0
    execution_sections = execution.get("execution_sections", {})
    execution_readiness = "unknown"
    if isinstance(execution_sections, dict) and execution_sections:
        backpack_enabled = bool((execution_sections.get("backpack_execution") or {}).get("enabled"))
        drift_enabled = bool((execution_sections.get("drift_execution") or {}).get("enabled"))
        execution_readiness = "enabled" if (backpack_enabled or drift_enabled) else "disabled"
    confluence_score = (
        (1 if chart else 0)
        + market_signal_count
        + indicator_signal_count
        + (1 if explicit_invalidation else 0)
        + (1 if execution_readiness == "enabled" else 0)
        - (1 if degraded_nodes else 0)
        - (1 if caution_level == "high" else 0)
    )
    if confluence_score >= 3:
        confluence_strength = "high"
    elif confluence_score >= 1:
        confluence_strength = "medium"
    else:
        confluence_strength = "low"

    fresh_headline_count = (
        len([item for item in news_items if isinstance(item, dict) and item.get("is_new")])
        if isinstance(news_items, list)
        else 0
    )
    if fresh_headline_count >= 2:
        news_fragility = "high"
    elif fresh_headline_count == 1:
        news_fragility = "elevated"
    else:
        news_fragility = "stable"

    symbol, timeframe = _extract_symbol_and_timeframe(observations, market_context)
    details = {
        "resolved_symbol": symbol,
        "resolved_timeframe": timeframe,
        "explicit_invalidation_present": explicit_invalidation,
        "invalidation_quality": invalidation_quality,
        "invalidation_markers": invalidation_labels,
        "degraded_nodes": degraded_nodes,
        "rsi_value": rsi_value,
        "fresh_headline_count": fresh_headline_count,
        "news_fragility": news_fragility,
        "execution_readiness": execution_readiness,
        "confluence_strength": confluence_strength,
        "caution_level": caution_level,
    }
    return flags, details


async def run_risk_review_node(
    context: AgentNodeExecutionContext,
    plan: AgentPipelineNodePlan,
) -> AgentPipelineNodeResult:
    flags, details = _derive_risk_flags(
        user_input=context.user_input,
        observations=context.observations,
        market_context=context.market_context or {},
    )
    loop_trace = [
        {
            "phase": "Reason-Act-Critique-Observe",
            "reason": "Review the accumulated pipeline observations through a downside and invalidation lens.",
            "actions": [],
            "critique": "The node stayed read-only and did not fetch any new market data or mutate state.",
            "observe": {
                "flag_count": len(flags),
                "caution_level": details.get("caution_level"),
                "resolved_symbol": details.get("resolved_symbol"),
            },
        }
    ]
    summary_payload = {
        **details,
        "risk_flags": flags,
        "risk_summary": {
            "invalidation_quality": details.get("invalidation_quality"),
            "confluence_strength": details.get("confluence_strength"),
            "news_fragility": details.get("news_fragility"),
            "execution_readiness": details.get("execution_readiness"),
            "caution_level": details.get("caution_level"),
        },
        "loop_trace": loop_trace,
        "retryable": False,
    }
    return AgentPipelineNodeResult(
        status="completed",
        summary="Risk review node assessed invalidation, caution flags, and setup fragility.",
        metadata=summary_payload,
        system_prompt_addition=_build_prompt_addition(summary_payload),
    )
