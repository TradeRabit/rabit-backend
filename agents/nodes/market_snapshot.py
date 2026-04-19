"""Composable market-snapshot pipeline node."""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from agents.core.graph_executor import AgentNodeExecutionContext, AgentPipelineNodeResult
from agents.core.pipeline import AgentPipelineNodePlan
from config.settings import settings


def _extract_requested_symbol(user_input: str, market_context: Dict[str, Any]) -> Optional[str]:
    """Infer the desired trading symbol from text or market context."""
    tracked_symbols = [symbol.strip().upper() for symbol in settings.TRADING_ASSETS if symbol.strip()]
    text = (user_input or "").upper()

    for symbol in tracked_symbols:
        if re.search(rf"\b{re.escape(symbol)}\b", text):
            return symbol

    context_symbol = str(market_context.get("symbol") or "").strip().upper()
    return context_symbol or None


def _resolve_snapshot_symbol(context: AgentNodeExecutionContext) -> Optional[str]:
    """Pick the best symbol for the market snapshot."""
    chart_observation = context.observations.get("chart_analysis", {})
    effective_symbol = str(chart_observation.get("effective_symbol") or "").strip().upper()
    if effective_symbol:
        return effective_symbol

    requested_symbol = str(chart_observation.get("requested_symbol") or "").strip().upper()
    if requested_symbol:
        return requested_symbol

    return _extract_requested_symbol(context.user_input, context.market_context or {})


async def _call_required_tool(
    context: AgentNodeExecutionContext,
    tool_name: str,
    arguments: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any], Optional[str]]:
    """Call one tool through the shared tool caller."""
    if context.call_tool is None:
        return False, {}, "No tool caller available for market snapshot node."

    result = await context.call_tool(tool_name, arguments)
    if getattr(result, "success", False):
        return True, getattr(result, "data", {}) or {}, None
    return False, {}, getattr(result, "error", None) or "Unknown tool failure"


def _normalize_price_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a get_price tool result into a compact snapshot."""
    if payload.get("success") is False:
        return {}

    snapshot = {
        "symbol": payload.get("symbol"),
        "price": payload.get("price"),
        "change_24h": payload.get("change_24h"),
        "volume_24h": payload.get("volume_24h"),
        "open_interest": payload.get("open_interest"),
        "funding_rate": payload.get("funding_rate"),
        "timestamp": payload.get("timestamp"),
    }
    return {key: value for key, value in snapshot.items() if value is not None}


def _extract_news_items(payload: Dict[str, Any], symbol: str) -> List[Dict[str, Any]]:
    """Extract a normalized list of news items for one symbol."""
    results = payload.get("results", payload)
    if not isinstance(results, dict):
        return []

    raw_items = results.get(symbol, [])
    if not isinstance(raw_items, list):
        return []

    normalized: List[Dict[str, Any]] = []
    for item in raw_items[:10]:
        if not isinstance(item, dict):
            continue
        normalized.append(
            {
                "title": item.get("title", ""),
                "source": item.get("source", ""),
                "date": item.get("date", ""),
                "detected_at": item.get("detected_at", ""),
                "is_new": item.get("is_new"),
            }
        )
    return normalized


def _build_market_snapshot_prompt_addition(summary: Dict[str, Any]) -> str:
    """Format backend market observations into a trusted prompt addition."""
    compact = json.dumps(summary, ensure_ascii=False)
    return (
        "Internal market-snapshot node observations:\n"
        f"{compact}\n"
        "Treat these observations as trusted backend-generated market context. "
        "Use them to strengthen the final answer without claiming unsupported live feed access."
    )


async def run_market_snapshot_node(
    context: AgentNodeExecutionContext,
    plan: AgentPipelineNodePlan,
) -> AgentPipelineNodeResult:
    """Capture a compact read-only market snapshot for the current asset."""
    symbol = _resolve_snapshot_symbol(context)
    if not symbol:
        return AgentPipelineNodeResult(
            status="skipped",
            summary="Market snapshot node skipped because no asset symbol could be resolved.",
            metadata={"resolved_symbol": None},
        )

    errors: List[str] = []
    loop_trace: List[Dict[str, Any]] = []

    ok_price, price_payload, price_error = await _call_required_tool(context, "get_price", {"symbol": symbol})
    if price_error:
        errors.append(price_error)

    max_headlines = int(plan.config.get("max_headlines", 3) or 3)
    ok_news, news_payload, news_error = await _call_required_tool(
        context,
        "search_news_by_symbols",
        {"symbols": symbol, "max_results": max_headlines},
    )
    if news_error:
        errors.append(news_error)

    price_snapshot = _normalize_price_payload(price_payload if ok_price else {})
    news_items = _extract_news_items(news_payload if ok_news else {}, symbol)[:max_headlines]

    loop_trace.append(
        {
            "phase": "Reason-Act-Critique-Observe",
            "reason": "Gather a compact market snapshot for the active asset before the final response.",
            "actions": ["get_price", "search_news_by_symbols"],
            "critique": "The node stayed read-only and limited itself to live price plus recent symbol news.",
            "observe": {
                "resolved_symbol": symbol,
                "price_available": ok_price,
                "news_count": len(news_items),
                "headline_titles": [item.get("title", "") for item in news_items],
            },
        }
    )

    summary_payload = {
        "resolved_symbol": symbol,
        "price_snapshot": price_snapshot,
        "news_headlines": news_items,
        "loop_trace": loop_trace,
        "errors": errors,
    }

    status = "completed" if (price_snapshot or news_items) and not errors else "degraded"
    if not price_snapshot and not news_items:
        status = "skipped"

    if status == "completed":
        summary = "Market snapshot node gathered live price and recent headlines."
    elif status == "degraded":
        summary = "Market snapshot node gathered partial context with some degraded steps."
    else:
        summary = "Market snapshot node could not gather useful context for the current asset."

    return AgentPipelineNodeResult(
        status=status,
        summary=summary,
        metadata=summary_payload,
        system_prompt_addition=(
            _build_market_snapshot_prompt_addition(summary_payload)
            if status != "skipped"
            else ""
        ),
    )
