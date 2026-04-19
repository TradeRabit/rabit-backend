"""Composable research-snapshot pipeline node."""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from agents.core.graph_executor import AgentNodeExecutionContext, AgentPipelineNodeResult
from agents.pipeline.pipeline import AgentPipelineNodePlan
from config.settings import settings


RESEARCH_LIKE_INTENTS = {
    "news_impact",
    "macro_context",
    "regulatory_check",
    "research",
    "plan_or_strategy",
    "education",
}


def _extract_requested_symbol(user_input: str, market_context: Dict[str, Any]) -> Optional[str]:
    """Infer the desired trading symbol from text or market context."""
    tracked_symbols = [symbol.strip().upper() for symbol in settings.TRADING_ASSETS if symbol.strip()]
    text = (user_input or "").upper()

    for symbol in tracked_symbols:
        if re.search(rf"\b{re.escape(symbol)}\b", text):
            return symbol

    context_symbol = str(market_context.get("symbol") or "").strip().upper()
    return context_symbol or None


async def _call_required_tool(
    context: AgentNodeExecutionContext,
    tool_name: str,
    arguments: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any], Optional[str]]:
    """Call one tool through the shared tool caller."""
    if context.call_tool is None:
        return False, {}, "No tool caller available for research snapshot node."

    result = await context.call_tool(tool_name, arguments)
    if getattr(result, "success", False):
        return True, getattr(result, "data", {}) or {}, None
    return False, {}, getattr(result, "error", None) or "Unknown tool failure"


def _extract_news_items(payload: Dict[str, Any], symbol: Optional[str]) -> List[Dict[str, Any]]:
    """Extract normalized news items from symbol or trending payloads."""
    if symbol:
        results = payload.get("results", payload)
        if not isinstance(results, dict):
            return []
        raw_items = results.get(symbol, [])
    else:
        raw_items = payload.get("results", [])

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
                "url": item.get("url", ""),
            }
        )
    return normalized


def _extract_search_results(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract normalized web search results."""
    raw_items = payload.get("results", [])
    if not isinstance(raw_items, list):
        return []

    normalized: List[Dict[str, Any]] = []
    for item in raw_items[:10]:
        if not isinstance(item, dict):
            continue
        normalized.append(
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("snippet", ""),
            }
        )
    return normalized


def _build_research_snapshot_prompt_addition(summary: Dict[str, Any]) -> str:
    """Format backend research observations into a trusted prompt addition."""
    compact = json.dumps(summary, ensure_ascii=False)
    return (
        "Internal research-snapshot node observations:\n"
        f"{compact}\n"
        "Treat these observations as trusted backend-generated research context. "
        "Use them to strengthen the final answer without claiming unsupported browsing or feed access."
    )


async def run_research_snapshot_node(
    context: AgentNodeExecutionContext,
    plan: AgentPipelineNodePlan,
) -> AgentPipelineNodeResult:
    """Capture a compact research snapshot for research-like requests."""
    intent = str(getattr(context.intent_context, "intent", "") or "").strip()
    if intent not in RESEARCH_LIKE_INTENTS:
        return AgentPipelineNodeResult(
            status="skipped",
            summary="Research snapshot node skipped because the request is not research-like.",
            metadata={"intent": intent, "retryable": False},
        )

    symbol = _extract_requested_symbol(context.user_input, context.market_context or {})
    errors: List[str] = []
    loop_trace: List[Dict[str, Any]] = []
    news_items: List[Dict[str, Any]] = []
    web_results: List[Dict[str, Any]] = []

    max_headlines = int(plan.config.get("max_headlines", 3) or 3)
    max_search_results = int(plan.config.get("max_search_results", 3) or 3)

    if symbol:
        ok_news, news_payload, news_error = await _call_required_tool(
            context,
            "search_news_by_symbols",
            {"symbols": symbol, "max_results": max_headlines},
        )
        if news_error:
            errors.append(news_error)
        news_items = _extract_news_items(news_payload if ok_news else {}, symbol)[:max_headlines]
        actions = ["search_news_by_symbols"]
        critique = "The node preferred symbol-specific news first because the request is asset-sensitive."
    else:
        ok_news, news_payload, news_error = await _call_required_tool(
            context,
            "get_trending_news",
            {"timeframe": "24h", "max_results": max_headlines},
        )
        if news_error:
            errors.append(news_error)
        news_items = _extract_news_items(news_payload if ok_news else {}, None)[:max_headlines]
        actions = ["get_trending_news"]
        critique = "The node preferred a compact trending-news view because no specific symbol was resolved."

    ok_search, search_payload, search_error = await _call_required_tool(
        context,
        "web_search",
        {"query": context.user_input, "max_results": max_search_results},
    )
    if search_error:
        errors.append(search_error)
    web_results = _extract_search_results(search_payload if ok_search else {})[:max_search_results]
    actions.append("web_search")

    loop_trace.append(
        {
            "phase": "Reason-Act-Critique-Observe",
            "reason": "Gather a compact research snapshot before the final response.",
            "actions": actions,
            "critique": critique,
            "observe": {
                "resolved_symbol": symbol,
                "news_count": len(news_items),
                "web_result_count": len(web_results),
                "headline_titles": [item.get("title", "") for item in news_items],
                "web_titles": [item.get("title", "") for item in web_results],
            },
        }
    )

    summary_payload = {
        "intent": intent,
        "resolved_symbol": symbol,
        "news_headlines": news_items,
        "web_results": web_results,
        "loop_trace": loop_trace,
        "errors": errors,
        "retryable": bool(errors),
    }

    status = "completed" if (news_items or web_results) and not errors else "degraded"
    if not news_items and not web_results:
        status = "skipped"

    if status == "completed":
        summary = "Research snapshot node gathered compact news and search context."
    elif status == "degraded":
        summary = "Research snapshot node gathered partial context with some degraded steps."
    else:
        summary = "Research snapshot node could not gather useful research context."

    return AgentPipelineNodeResult(
        status=status,
        summary=summary,
        metadata=summary_payload,
        system_prompt_addition=(
            _build_research_snapshot_prompt_addition(summary_payload)
            if status != "skipped"
            else ""
        ),
    )
