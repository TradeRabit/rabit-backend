"""Composable chart-analysis pipeline node."""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from config.settings import settings
from agents.core.graph_executor import AgentNodeExecutionContext, AgentPipelineNodeResult
from agents.core.pipeline import AgentPipelineNodePlan
from agents.tools.tradingview.indicators import INDICATOR_MAP


TIMEFRAME_PATTERNS = [
    (re.compile(r"\b(1m|1min|1 minute)\b", re.IGNORECASE), "1"),
    (re.compile(r"\b(5m|5min|5 minute)\b", re.IGNORECASE), "5"),
    (re.compile(r"\b(15m|15min|15 minute)\b", re.IGNORECASE), "15"),
    (re.compile(r"\b(30m|30min|30 minute)\b", re.IGNORECASE), "30"),
    (re.compile(r"\b(1h|1 hour|60m)\b", re.IGNORECASE), "60"),
    (re.compile(r"\b(4h|4 hour|240m)\b", re.IGNORECASE), "240"),
    (re.compile(r"\b(1d|1 day|daily)\b", re.IGNORECASE), "D"),
    (re.compile(r"\b(1w|1 week|weekly)\b", re.IGNORECASE), "W"),
    (re.compile(r"\b(1mo|1 month|monthly)\b", re.IGNORECASE), "M"),
]


def _extract_requested_symbol(user_input: str, market_context: Dict[str, Any]) -> Optional[str]:
    """Infer the desired trading symbol from text or market context."""
    tracked_symbols = [symbol.strip().upper() for symbol in settings.TRADING_ASSETS if symbol.strip()]
    text = (user_input or "").upper()

    for symbol in tracked_symbols:
        if re.search(rf"\b{re.escape(symbol)}\b", text):
            return symbol

    context_symbol = str(market_context.get("symbol") or "").strip().upper()
    return context_symbol or None


def _extract_requested_timeframe(user_input: str, market_context: Dict[str, Any]) -> Optional[str]:
    """Infer desired timeframe from the request or current context."""
    text = user_input or ""
    for pattern, normalized in TIMEFRAME_PATTERNS:
        if pattern.search(text):
            return normalized

    timeframe = str(market_context.get("timeframe") or "").strip().upper()
    return timeframe or None


def _extract_requested_indicators(user_input: str, indicator_hint: str = "") -> List[str]:
    """Infer requested indicators from text and router hint."""
    text = f"{user_input or ''} {indicator_hint or ''}".lower()
    requested: List[str] = []

    for short_name, full_name in INDICATOR_MAP.items():
        candidates = {short_name.lower(), full_name.lower()}
        if any(candidate in text for candidate in candidates):
            requested.append(full_name)

    # Preserve order while removing duplicates.
    deduped: List[str] = []
    for name in requested:
        if name not in deduped:
            deduped.append(name)
    return deduped


def _normalize_state_symbol(state: Dict[str, Any]) -> Optional[str]:
    symbol = str(state.get("symbol") or "").strip().upper()
    if not symbol:
        return None
    return re.sub(r"(USDT|USD|PERP)$", "", symbol)


def _normalize_state_timeframe(state: Dict[str, Any]) -> Optional[str]:
    timeframe = str(state.get("timeframe") or "").strip().upper()
    return timeframe or None


def _extract_state_indicators(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw = state.get("indicators") or []
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    return []


def _find_matching_indicator(indicators: List[Dict[str, Any]], expected_name: str) -> Optional[Dict[str, Any]]:
    expected = expected_name.lower()
    for indicator in indicators:
        name = str(indicator.get("name") or indicator.get("title") or "").strip().lower()
        short_name = str(indicator.get("short_name") or "").strip().lower()
        if expected in {name, short_name} or expected in name:
            return indicator
    return None


async def _call_required_tool(
    context: AgentNodeExecutionContext,
    tool_name: str,
    arguments: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any], Optional[str]]:
    """Call one tool through the shared tool caller."""
    if context.call_tool is None:
        return False, {}, "No tool caller available for chart analysis node."

    result = await context.call_tool(tool_name, arguments)
    if getattr(result, "success", False):
        return True, getattr(result, "data", {}) or {}, None
    return False, {}, getattr(result, "error", None) or "Unknown tool failure"


def _build_chart_prompt_addition(summary: Dict[str, Any]) -> str:
    """Format backend chart observations into a trusted prompt addition."""
    compact = json.dumps(summary, ensure_ascii=False)
    return (
        "Internal chart-analysis node observations:\n"
        f"{compact}\n"
        "Treat these observations as trusted backend-generated chart context. "
        "Do not claim any chart-writing action was taken."
    )


async def run_chart_analysis_node(
    context: AgentNodeExecutionContext,
    plan: AgentPipelineNodePlan,
) -> AgentPipelineNodeResult:
    """Execute a bounded chart-analysis loop without allowing chart writing."""
    user_input = context.user_input
    market_context = context.market_context or {}
    scope_mode = str(market_context.get("scope_mode") or "global").strip().lower()
    locked_symbol = str(market_context.get("symbol") or "").strip().upper() or None

    desired_symbol = _extract_requested_symbol(user_input, market_context)
    desired_timeframe = _extract_requested_timeframe(user_input, market_context)
    desired_indicators = _extract_requested_indicators(
        user_input,
        getattr(context.intent_context, "inferred_indicator_hint", ""),
    )

    loop_trace: List[Dict[str, Any]] = []
    errors: List[str] = []

    # Observe current state first.
    ok, state_payload, error = await _call_required_tool(context, "tv_get_state", {})
    if not ok:
        errors.append(error or "Failed to read TradingView state.")
        return AgentPipelineNodeResult(
            status="degraded",
            summary="Chart analysis node could not read the active TradingView state.",
            metadata={
                "errors": errors,
                "desired_symbol": desired_symbol,
                "desired_timeframe": desired_timeframe,
                "desired_indicators": desired_indicators,
            },
        )

    current_state = state_payload.get("data", state_payload)
    current_symbol = _normalize_state_symbol(current_state)
    current_timeframe = _normalize_state_timeframe(current_state)
    current_indicators = _extract_state_indicators(current_state)
    added_indicators: List[Dict[str, Any]] = []
    symbol_change_blocked = False

    # Step 1: align workspace
    align_actions: List[str] = []
    if desired_symbol and desired_symbol != current_symbol:
        if scope_mode == "locked_asset" and locked_symbol and desired_symbol != locked_symbol:
            symbol_change_blocked = True
        elif plan.config.get("allow_symbol_change_when_global", True):
            align_actions.append("set_symbol")

    if desired_timeframe and desired_timeframe != current_timeframe:
        align_actions.append("set_timeframe")

    if align_actions:
        reason = "Align the chart workspace with the requested symbol and timeframe."
        action_results: Dict[str, Any] = {}

        if "set_symbol" in align_actions and desired_symbol:
            ok, payload, error = await _call_required_tool(context, "tv_set_symbol", {"symbol": desired_symbol})
            action_results["set_symbol"] = {"success": ok, "error": error, "payload": payload}
            if not ok and error:
                errors.append(error)

        if "set_timeframe" in align_actions and desired_timeframe:
            ok, payload, error = await _call_required_tool(context, "tv_set_timeframe", {"timeframe": desired_timeframe})
            action_results["set_timeframe"] = {"success": ok, "error": error, "payload": payload}
            if not ok and error:
                errors.append(error)

        ok, state_payload, error = await _call_required_tool(context, "tv_get_state", {})
        if ok:
            current_state = state_payload.get("data", state_payload)
            current_symbol = _normalize_state_symbol(current_state)
            current_timeframe = _normalize_state_timeframe(current_state)
            current_indicators = _extract_state_indicators(current_state)
        elif error:
            errors.append(error)

        loop_trace.append(
            {
                "phase": "Reason-Act-Critique-Observe",
                "reason": reason,
                "actions": align_actions,
                "critique": "Workspace alignment attempted before reading indicator values.",
                "observe": {
                    "current_symbol": current_symbol,
                    "current_timeframe": current_timeframe,
                    "symbol_change_blocked": symbol_change_blocked,
                    "action_results": action_results,
                },
            }
        )
    elif symbol_change_blocked:
        loop_trace.append(
            {
                "phase": "Reason-Act-Critique-Observe",
                "reason": "Keep the chart inside the locked-asset boundary.",
                "actions": [],
                "critique": "Requested symbol change was blocked by locked asset scope.",
                "observe": {
                    "current_symbol": current_symbol,
                    "locked_symbol": locked_symbol,
                    "requested_symbol": desired_symbol,
                    "symbol_change_blocked": True,
                },
            }
        )

    # Step 2: prepare indicators
    missing_indicators = [
        indicator
        for indicator in desired_indicators
        if _find_matching_indicator(current_indicators, indicator) is None
    ]
    if missing_indicators and plan.config.get("allow_indicator_add", True):
        add_results: List[Dict[str, Any]] = []
        for indicator in missing_indicators:
            ok, payload, error = await _call_required_tool(
                context,
                "tv_add_indicator",
                {"indicator": indicator},
            )
            add_results.append(
                {
                    "indicator": indicator,
                    "success": ok,
                    "error": error,
                    "entity_id": payload.get("entity_id"),
                }
            )
            if ok:
                added_indicators.append(
                    {
                        "indicator": indicator,
                        "entity_id": payload.get("entity_id"),
                    }
                )
            elif error:
                errors.append(error)

        ok, state_payload, error = await _call_required_tool(context, "tv_get_state", {})
        if ok:
            current_state = state_payload.get("data", state_payload)
            current_indicators = _extract_state_indicators(current_state)
        elif error:
            errors.append(error)

        loop_trace.append(
            {
                "phase": "Reason-Act-Critique-Observe",
                "reason": "Add missing indicators before reading their values.",
                "actions": ["tv_add_indicator"],
                "critique": "Indicators were added only when missing from the current workspace.",
                "observe": {
                    "requested_indicators": desired_indicators,
                    "missing_indicators": missing_indicators,
                    "added_indicators": add_results,
                },
            }
        )

    # Step 3: gather values
    ok_quote, quote_payload, quote_error = await _call_required_tool(context, "tv_get_quote", {})
    if quote_error:
        errors.append(quote_error)
    ok_values, values_payload, values_error = await _call_required_tool(context, "tv_get_indicator_values", {})
    if values_error:
        errors.append(values_error)

    quote_data = quote_payload.get("data", quote_payload) if ok_quote else {}
    indicator_values = values_payload.get("data", values_payload) if ok_values else {}

    loop_trace.append(
        {
            "phase": "Reason-Act-Critique-Observe",
            "reason": "Collect the current quote and indicator values for the final chart read.",
            "actions": ["tv_get_quote", "tv_get_indicator_values"],
            "critique": (
                "The node collected only read-side values and skipped drawing or alert tools."
            ),
            "observe": {
                "quote_available": ok_quote,
                "indicator_values_available": ok_values,
                "indicator_value_keys": list(indicator_values.keys())[:12] if isinstance(indicator_values, dict) else [],
            },
        }
    )

    summary_payload = {
        "scope_mode": scope_mode,
        "requested_symbol": desired_symbol,
        "effective_symbol": current_symbol,
        "locked_symbol": locked_symbol,
        "symbol_change_blocked": symbol_change_blocked,
        "requested_timeframe": desired_timeframe,
        "effective_timeframe": current_timeframe,
        "requested_indicators": desired_indicators,
        "added_indicators": added_indicators,
        "quote": quote_data,
        "indicator_values": indicator_values,
        "loop_trace": loop_trace,
        "errors": errors,
    }

    status = "completed" if not errors else "degraded"
    summary = (
        "Chart analysis node prepared chart context from TradingView."
        if status == "completed"
        else "Chart analysis node produced partial TradingView context with some degraded steps."
    )
    return AgentPipelineNodeResult(
        status=status,
        summary=summary,
        metadata=summary_payload,
        system_prompt_addition=_build_chart_prompt_addition(summary_payload),
    )

