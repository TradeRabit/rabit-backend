"""Composable chart-analysis pipeline node with analysis and write modes."""
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

LABELED_LEVEL_PATTERNS = [
    (re.compile(r"\b(support)\s*(?:at|around)?\s*\$?([\d,]+(?:\.\d+)?)", re.IGNORECASE), "#22C55E"),
    (re.compile(r"\b(resistance)\s*(?:at|around)?\s*\$?([\d,]+(?:\.\d+)?)", re.IGNORECASE), "#EF4444"),
    (re.compile(r"\b(entry)\s*(?:at|around)?\s*\$?([\d,]+(?:\.\d+)?)", re.IGNORECASE), "#22C55E"),
    (re.compile(r"\b(target(?:\s*\d+)?)\s*(?:at|around)?\s*\$?([\d,]+(?:\.\d+)?)", re.IGNORECASE), "#F59E0B"),
    (re.compile(r"\b(stop(?:\s*loss)?)\s*(?:at|around)?\s*\$?([\d,]+(?:\.\d+)?)", re.IGNORECASE), "#EF4444"),
    (re.compile(r"\b(invalidation)\s*(?:at|around)?\s*\$?([\d,]+(?:\.\d+)?)", re.IGNORECASE), "#EF4444"),
    (re.compile(r"\b(validation)\s*(?:at|around)?\s*\$?([\d,]+(?:\.\d+)?)", re.IGNORECASE), "#22C55E"),
]

PRICE_PATTERN = re.compile(r"(?<![\w-])\$?(\d{1,6}(?:,\d{3})*(?:\.\d+)?)(?![\w-])")
ISO_DATE_PATTERN = re.compile(r"\b\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2})?(?:Z)?)?\b")


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


def _extract_iso_dates(user_input: str) -> List[str]:
    """Extract ISO-like dates from the request."""
    return [match.group(0).replace(" ", "T") for match in ISO_DATE_PATTERN.finditer(user_input or "")]


def _extract_prices(user_input: str) -> List[float]:
    """Extract numeric prices from free-form text."""
    prices: List[float] = []
    for match in PRICE_PATTERN.finditer(user_input or ""):
        raw = match.group(1).replace(",", "")
        try:
            prices.append(float(raw))
        except ValueError:
            continue
    return prices


def _is_clear_request(user_input: str) -> bool:
    text = (user_input or "").lower()
    return bool(
        re.search(r"\b(clear|wipe|reset|remove)\b", text)
        and re.search(r"\b(drawings?|lines?|annotations?|chart)\b", text)
    )


def _looks_like_trend_line_request(user_input: str) -> bool:
    text = (user_input or "").lower()
    return bool(
        re.search(r"\b(trend line|draw line|plot line|annotate line)\b", text)
        or (
            re.search(r"\b(from)\b", text)
            and re.search(r"\b(to)\b", text)
            and "line" in text
        )
    )


def _extract_labeled_horizontal_levels(user_input: str) -> List[Dict[str, Any]]:
    """Extract horizontal level requests with labels and colors."""
    text = user_input or ""
    levels: List[Dict[str, Any]] = []
    seen: set[tuple[str, float]] = set()

    for pattern, color in LABELED_LEVEL_PATTERNS:
        for match in pattern.finditer(text):
            label = match.group(1).strip()
            raw_price = match.group(2).replace(",", "")
            try:
                price = float(raw_price)
            except ValueError:
                continue
            key = (label.lower(), price)
            if key in seen:
                continue
            seen.add(key)
            levels.append(
                {
                    "type": "horizontal_line",
                    "price": price,
                    "text": label.title(),
                    "color": color,
                    "width": 2,
                    "source": "labeled_level",
                }
            )

    if levels:
        return levels

    generic_write = bool(
        re.search(r"\b(draw|mark|plot|annotate)\b", text.lower())
        and re.search(r"\b(line|level|support|resistance|entry|target|stop|invalidation|validation)\b", text.lower())
    )
    generic_prices = _extract_prices(text)
    if generic_write and generic_prices:
        return [
            {
                "type": "horizontal_line",
                "price": generic_prices[0],
                "text": None,
                "color": "#FD4C01",
                "width": 2,
                "source": "generic_level",
            }
        ]

    return []


def _extract_trend_line_request(user_input: str) -> Optional[Dict[str, Any]]:
    """Extract one explicit trend-line request when enough coordinates exist."""
    if not _looks_like_trend_line_request(user_input):
        return None

    dates = _extract_iso_dates(user_input)
    prices = _extract_prices(user_input)
    if len(dates) < 2 or len(prices) < 2:
        return None

    return {
        "type": "trend_line",
        "price1": prices[0],
        "time1": dates[0],
        "price2": prices[1],
        "time2": dates[1],
        "color": "#FD4C01",
        "width": 2,
    }


async def _call_required_tool(
    context: AgentNodeExecutionContext,
    tool_name: str,
    arguments: Dict[str, Any],
) -> Tuple[bool, Dict[str, Any], Optional[str]]:
    """Call one tool through the shared tool caller."""
    if context.call_tool is None:
        return False, {}, "No tool caller available for chart node."

    result = await context.call_tool(tool_name, arguments)
    if getattr(result, "success", False):
        return True, getattr(result, "data", {}) or {}, None
    return False, {}, getattr(result, "error", None) or "Unknown tool failure"


def _build_chart_prompt_addition(summary: Dict[str, Any]) -> str:
    """Format backend chart observations into a trusted prompt addition."""
    compact = json.dumps(summary, ensure_ascii=False)
    chart_mode = str(summary.get("chart_mode") or "analysis").strip().lower()
    header = (
        "Internal chart-write node observations:"
        if chart_mode == "write"
        else "Internal chart-analysis node observations:"
    )
    return (
        f"{header}\n"
        f"{compact}\n"
        "Treat these observations as trusted backend-generated chart context. "
        "Only describe mutations or chart evidence that this node actually produced."
    )


async def _observe_chart_state(
    context: AgentNodeExecutionContext,
    errors: List[str],
) -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[str], List[Dict[str, Any]]]:
    """Fetch the current chart state and normalize the key fields."""
    ok, state_payload, error = await _call_required_tool(context, "tv_get_state", {})
    if not ok:
        errors.append(error or "Failed to read TradingView state.")
        return None, None, None, []

    current_state = state_payload.get("data", state_payload)
    current_symbol = _normalize_state_symbol(current_state)
    current_timeframe = _normalize_state_timeframe(current_state)
    current_indicators = _extract_state_indicators(current_state)
    return current_state, current_symbol, current_timeframe, current_indicators


async def _align_workspace(
    *,
    context: AgentNodeExecutionContext,
    plan: AgentPipelineNodePlan,
    user_input: str,
    market_context: Dict[str, Any],
    current_symbol: Optional[str],
    current_timeframe: Optional[str],
    errors: List[str],
    loop_trace: List[Dict[str, Any]],
) -> Tuple[Optional[str], Optional[str], bool]:
    """Align symbol/timeframe before chart work."""
    scope_mode = str(market_context.get("scope_mode") or "global").strip().lower()
    locked_symbol = str(market_context.get("symbol") or "").strip().upper() or None
    desired_symbol = _extract_requested_symbol(user_input, market_context)
    desired_timeframe = _extract_requested_timeframe(user_input, market_context)
    symbol_change_blocked = False
    align_actions: List[str] = []

    if desired_symbol and desired_symbol != current_symbol:
        if scope_mode == "locked_asset" and locked_symbol and desired_symbol != locked_symbol:
            symbol_change_blocked = True
        elif plan.config.get("allow_symbol_change_when_global", True):
            align_actions.append("set_symbol")

    if desired_timeframe and desired_timeframe != current_timeframe:
        align_actions.append("set_timeframe")

    if align_actions:
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

        _, current_symbol, current_timeframe, _ = await _observe_chart_state(context, errors)
        loop_trace.append(
            {
                "phase": "Reason-Act-Critique-Observe",
                "reason": "Align the chart workspace with the requested symbol and timeframe.",
                "actions": align_actions,
                "critique": "Workspace alignment happened before reading or mutating the chart.",
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

    return current_symbol, current_timeframe, symbol_change_blocked


async def _run_analysis_mode(
    context: AgentNodeExecutionContext,
    plan: AgentPipelineNodePlan,
) -> AgentPipelineNodeResult:
    """Existing chart read-side specialist behavior."""
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
    added_indicators: List[Dict[str, Any]] = []

    current_state, current_symbol, current_timeframe, current_indicators = await _observe_chart_state(context, errors)
    if current_state is None:
        return AgentPipelineNodeResult(
            status="degraded",
            summary="Chart specialist node could not read the active TradingView state.",
            metadata={
                "chart_mode": "analysis",
                "errors": errors,
                "requested_symbol": desired_symbol,
                "requested_timeframe": desired_timeframe,
                "requested_indicators": desired_indicators,
            },
        )

    current_symbol, current_timeframe, symbol_change_blocked = await _align_workspace(
        context=context,
        plan=plan,
        user_input=user_input,
        market_context=market_context,
        current_symbol=current_symbol,
        current_timeframe=current_timeframe,
        errors=errors,
        loop_trace=loop_trace,
    )

    _, current_symbol, current_timeframe, current_indicators = await _observe_chart_state(context, errors)
    current_indicators = current_indicators or []

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

        _, _, _, current_indicators = await _observe_chart_state(context, errors)
        current_indicators = current_indicators or []
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
            "critique": "The node collected only read-side values and skipped drawing or alert tools.",
            "observe": {
                "quote_available": ok_quote,
                "indicator_values_available": ok_values,
                "indicator_value_keys": list(indicator_values.keys())[:12] if isinstance(indicator_values, dict) else [],
            },
        }
    )

    summary_payload = {
        "chart_mode": "analysis",
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
        "Chart specialist node prepared chart analysis context from TradingView."
        if status == "completed"
        else "Chart specialist node produced partial TradingView analysis context with some degraded steps."
    )
    return AgentPipelineNodeResult(
        status=status,
        summary=summary,
        metadata=summary_payload,
        system_prompt_addition=_build_chart_prompt_addition(summary_payload),
    )


async def _run_write_mode(
    context: AgentNodeExecutionContext,
    plan: AgentPipelineNodePlan,
) -> AgentPipelineNodeResult:
    """Controlled chart mutation workflow inside the same chart node."""
    user_input = context.user_input
    market_context = context.market_context or {}
    scope_mode = str(market_context.get("scope_mode") or "global").strip().lower()
    locked_symbol = str(market_context.get("symbol") or "").strip().upper() or None
    desired_symbol = _extract_requested_symbol(user_input, market_context)
    desired_timeframe = _extract_requested_timeframe(user_input, market_context)

    loop_trace: List[Dict[str, Any]] = []
    errors: List[str] = []

    current_state, current_symbol, current_timeframe, _ = await _observe_chart_state(context, errors)
    if current_state is None:
        return AgentPipelineNodeResult(
            status="degraded",
            summary="Chart specialist node could not read the active TradingView state before attempting chart writes.",
            metadata={
                "chart_mode": "write",
                "errors": errors,
                "requested_symbol": desired_symbol,
                "requested_timeframe": desired_timeframe,
            },
        )

    current_symbol, current_timeframe, symbol_change_blocked = await _align_workspace(
        context=context,
        plan=plan,
        user_input=user_input,
        market_context=market_context,
        current_symbol=current_symbol,
        current_timeframe=current_timeframe,
        errors=errors,
        loop_trace=loop_trace,
    )

    clear_requested = _is_clear_request(user_input)
    horizontal_levels = _extract_labeled_horizontal_levels(user_input)
    trend_line = _extract_trend_line_request(user_input)

    requested_actions: List[str] = []
    if clear_requested:
        requested_actions.append("clear_drawings")
    if horizontal_levels:
        requested_actions.append("draw_horizontal_line")
    if trend_line:
        requested_actions.append("draw_trend_line")

    unmet_requirements: List[str] = []
    if _looks_like_trend_line_request(user_input) and trend_line is None:
        unmet_requirements.append("Trend-line requests need two prices and two ISO dates or datetimes.")

    if not requested_actions:
        if not unmet_requirements:
            unmet_requirements.append("No explicit writable chart action could be extracted from the request.")
        summary_payload = {
            "chart_mode": "write",
            "scope_mode": scope_mode,
            "requested_symbol": desired_symbol,
            "effective_symbol": current_symbol,
            "locked_symbol": locked_symbol,
            "symbol_change_blocked": symbol_change_blocked,
            "requested_timeframe": desired_timeframe,
            "effective_timeframe": current_timeframe,
            "requested_actions": requested_actions,
            "applied_actions": [],
            "unmet_requirements": unmet_requirements,
            "loop_trace": loop_trace,
            "errors": errors,
        }
        return AgentPipelineNodeResult(
            status="degraded",
            summary="Chart specialist node did not apply chart writes because the request was not concrete enough.",
            metadata=summary_payload,
            system_prompt_addition=_build_chart_prompt_addition(summary_payload),
        )

    applied_actions: List[Dict[str, Any]] = []
    action_results: List[Dict[str, Any]] = []

    if clear_requested:
        ok, payload, error = await _call_required_tool(context, "tv_clear_drawings", {})
        action_result = {
            "action": "clear_drawings",
            "success": ok,
            "error": error,
            "payload": payload,
        }
        action_results.append(action_result)
        if ok:
            applied_actions.append({"action": "clear_drawings"})
        elif error:
            errors.append(error)

    for level in horizontal_levels:
        ok, payload, error = await _call_required_tool(
            context,
            "tv_draw_horizontal_line",
            {
                "price": level["price"],
                "color": level["color"],
                "width": level["width"],
                "text": level["text"],
            },
        )
        action_result = {
            "action": "draw_horizontal_line",
            "price": level["price"],
            "text": level["text"],
            "success": ok,
            "error": error,
            "drawing_id": payload.get("drawing_id"),
        }
        action_results.append(action_result)
        if ok:
            applied_actions.append(
                {
                    "action": "draw_horizontal_line",
                    "price": level["price"],
                    "text": level["text"],
                    "drawing_id": payload.get("drawing_id"),
                }
            )
        elif error:
            errors.append(error)

    if trend_line:
        ok, payload, error = await _call_required_tool(
            context,
            "tv_draw_line",
            {
                "price1": trend_line["price1"],
                "time1": trend_line["time1"],
                "price2": trend_line["price2"],
                "time2": trend_line["time2"],
                "color": trend_line["color"],
                "width": trend_line["width"],
            },
        )
        action_result = {
            "action": "draw_trend_line",
            "price1": trend_line["price1"],
            "time1": trend_line["time1"],
            "price2": trend_line["price2"],
            "time2": trend_line["time2"],
            "success": ok,
            "error": error,
            "drawing_id": payload.get("drawing_id"),
        }
        action_results.append(action_result)
        if ok:
            applied_actions.append(
                {
                    "action": "draw_trend_line",
                    "price1": trend_line["price1"],
                    "time1": trend_line["time1"],
                    "price2": trend_line["price2"],
                    "time2": trend_line["time2"],
                    "drawing_id": payload.get("drawing_id"),
                }
            )
        elif error:
            errors.append(error)

    loop_trace.append(
        {
            "phase": "Reason-Act-Critique-Observe",
            "reason": "Apply only the explicit chart mutations requested by the user.",
            "actions": requested_actions,
            "critique": "The node limited mutations to drawings and optional chart clearing, with no alert creation or indicator changes.",
            "observe": {
                "applied_actions": applied_actions,
                "action_results": action_results,
                "symbol_change_blocked": symbol_change_blocked,
            },
        }
    )

    screenshot_payload: Dict[str, Any] = {}
    screenshot_requested = bool(plan.config.get("capture_screenshot_after_write", True))
    if screenshot_requested and applied_actions:
        ok, payload, error = await _call_required_tool(context, "tv_capture_screenshot", {"region": "chart"})
        if ok:
            screenshot_payload = payload
        elif error:
            errors.append(error)
        loop_trace.append(
            {
                "phase": "Reason-Act-Critique-Observe",
                "reason": "Capture the resulting chart state after mutation.",
                "actions": ["tv_capture_screenshot"] if screenshot_requested else [],
                "critique": "Screenshot capture is used to confirm the resulting chart state for the UI and final answer.",
                "observe": {
                    "screenshot_available": ok,
                    "screenshot_url": payload.get("screenshot_url") if ok else None,
                },
            }
        )

    summary_payload = {
        "chart_mode": "write",
        "scope_mode": scope_mode,
        "requested_symbol": desired_symbol,
        "effective_symbol": current_symbol,
        "locked_symbol": locked_symbol,
        "symbol_change_blocked": symbol_change_blocked,
        "requested_timeframe": desired_timeframe,
        "effective_timeframe": current_timeframe,
        "requested_actions": requested_actions,
        "applied_actions": applied_actions,
        "unmet_requirements": unmet_requirements,
        "screenshot": screenshot_payload.get("data", screenshot_payload),
        "loop_trace": loop_trace,
        "errors": errors,
    }
    status = "completed" if applied_actions and not errors else "degraded"
    summary = (
        "Chart specialist node applied controlled chart writes in TradingView."
        if status == "completed"
        else "Chart specialist node attempted chart writes but some requested changes were incomplete or degraded."
    )
    return AgentPipelineNodeResult(
        status=status,
        summary=summary,
        metadata=summary_payload,
        system_prompt_addition=_build_chart_prompt_addition(summary_payload),
    )


async def run_chart_analysis_node(
    context: AgentNodeExecutionContext,
    plan: AgentPipelineNodePlan,
) -> AgentPipelineNodeResult:
    """Execute the chart specialist in either analysis or write mode."""
    chart_mode = str(plan.config.get("chart_mode") or "analysis").strip().lower()
    if chart_mode == "write" and plan.config.get("allow_chart_write", False):
        return await _run_write_mode(context, plan)
    return await _run_analysis_mode(context, plan)
