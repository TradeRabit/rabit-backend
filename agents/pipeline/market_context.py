"""Helpers for frontend-supplied market context."""
from typing import Any, Dict, List, Optional


VALID_SCOPE_MODES = {"locked_asset", "global"}
VALID_TREND_BIAS = {"bullish", "bearish", "neutral", "mixed", "unknown"}
VALID_STRUCTURE_POSITION = {
    "above_support",
    "below_support",
    "near_support",
    "near_resistance",
    "breakout",
    "breakdown",
    "mid_range",
    "unknown",
}
VALID_VOLATILITY_REGIME = {"low", "medium", "high", "unknown"}
VALID_MOMENTUM_STATE = {"strong", "weakening", "improving", "flat", "unknown"}


def _normalize_string(value: Any) -> Optional[str]:
    """Normalize optional string values."""
    text = str(value).strip() if value is not None else ""
    return text or None


def _normalize_string_list(value: Any) -> List[str]:
    """Normalize a list of simple string values."""
    if not isinstance(value, list):
        return []
    normalized: List[str] = []
    for item in value:
        text = _normalize_string(item)
        if text:
            normalized.append(text)
    return normalized


def normalize_market_context(raw: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Normalize frontend-provided market context into a stable dict shape."""
    payload = raw if isinstance(raw, dict) else {}

    scope_mode = str(payload.get("scope_mode", "global")).strip().lower()
    if scope_mode not in VALID_SCOPE_MODES:
        scope_mode = "global"

    market_state_raw = payload.get("market_state", {})
    market_state_raw = market_state_raw if isinstance(market_state_raw, dict) else {}
    news_context_raw = payload.get("news_context", {})
    news_context_raw = news_context_raw if isinstance(news_context_raw, dict) else {}

    trend_bias = str(market_state_raw.get("trend_bias", "unknown")).strip().lower()
    if trend_bias not in VALID_TREND_BIAS:
        trend_bias = "unknown"

    structure_position = str(
        market_state_raw.get("structure_position", "unknown")
    ).strip().lower()
    if structure_position not in VALID_STRUCTURE_POSITION:
        structure_position = "unknown"

    volatility_regime = str(
        market_state_raw.get("volatility_regime", "unknown")
    ).strip().lower()
    if volatility_regime not in VALID_VOLATILITY_REGIME:
        volatility_regime = "unknown"

    momentum_state = str(market_state_raw.get("momentum_state", "unknown")).strip().lower()
    if momentum_state not in VALID_MOMENTUM_STATE:
        momentum_state = "unknown"

    return {
        "scope_mode": scope_mode,
        "asset_id": _normalize_string(payload.get("asset_id")),
        "symbol": _normalize_string(payload.get("symbol")),
        "asset_name": _normalize_string(payload.get("asset_name")),
        "exchange": _normalize_string(payload.get("exchange")),
        "timeframe": _normalize_string(payload.get("timeframe")),
        "source_screen": _normalize_string(payload.get("source_screen")),
        "watchlist_symbols": _normalize_string_list(payload.get("watchlist_symbols")),
        "market_state": {
            "trend_bias": trend_bias,
            "structure_position": structure_position,
            "volatility_regime": volatility_regime,
            "momentum_state": momentum_state,
            "summary": _normalize_string(market_state_raw.get("summary")),
        },
        "news_context": {
            "tail_titles": _normalize_string_list(news_context_raw.get("tail_titles"))[:5],
        },
    }


def get_market_context_guidance(context: Optional[Dict[str, Any]]) -> str:
    """Return prompt guidance derived from the normalized market context."""
    normalized = normalize_market_context(context)
    lines: List[str] = []

    scope_mode = normalized["scope_mode"]
    symbol = normalized.get("symbol")
    asset_name = normalized.get("asset_name")
    timeframe = normalized.get("timeframe")
    exchange = normalized.get("exchange")
    watchlist_symbols = normalized.get("watchlist_symbols") or []
    market_state = normalized.get("market_state", {})
    news_context = normalized.get("news_context", {})

    if scope_mode == "locked_asset":
        label = symbol or asset_name or "the locked asset"
        lines.append(
            f"The frontend is currently locked to {label}. Focus on that asset unless "
            "the user explicitly asks to move to another asset."
        )
    else:
        lines.append(
            "The frontend is in a global market mode. You may compare assets or scan "
            "broader market context when it helps the user's request."
        )

    if timeframe:
        lines.append(f"Prefer {timeframe} as the current working timeframe unless the user changes it.")
    if exchange:
        lines.append(f"Use {exchange} as the current market venue context when relevant.")
    if watchlist_symbols:
        lines.append(
            "The user watchlist currently includes: " + ", ".join(watchlist_symbols[:8]) + "."
        )

    trend_bias = market_state.get("trend_bias")
    structure_position = market_state.get("structure_position")
    volatility_regime = market_state.get("volatility_regime")
    momentum_state = market_state.get("momentum_state")
    summary = market_state.get("summary")

    state_parts = []
    if trend_bias and trend_bias != "unknown":
        state_parts.append(f"trend bias is {trend_bias}")
    if structure_position and structure_position != "unknown":
        state_parts.append(f"structure position is {structure_position}")
    if volatility_regime and volatility_regime != "unknown":
        state_parts.append(f"volatility regime is {volatility_regime}")
    if momentum_state and momentum_state != "unknown":
        state_parts.append(f"momentum state is {momentum_state}")
    if state_parts:
        lines.append("Current market-state context: " + ", ".join(state_parts) + ".")
    if summary:
        lines.append(f"Market-state summary: {summary}")

    tail_titles = news_context.get("tail_titles") if isinstance(news_context, dict) else []
    if tail_titles:
        joined = "; ".join(tail_titles[:5])
        lines.append(f"Recent relevant headlines: {joined}")

    return " ".join(lines).strip()
