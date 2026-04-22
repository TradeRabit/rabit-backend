"""Decision-support tools for sizing, scanning, and structured trade debriefs."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from agents.journal_debrief import get_trade_debrief_service
from agents.tools import ToolDefinition, ToolParameter, tool_registry
from agents.tools.core.runtime_context import (
    get_current_market_context,
    get_current_user_id,
)
from config.settings import settings
from ws.services import get_market_service
from ws.utils.categories import normalize_category


def _float_or_none(value: Optional[float]) -> Optional[float]:
    return None if value is None else float(value)


def _require_user_id() -> str:
    user_id = get_current_user_id()
    if not user_id:
        raise ValueError("This tool requires an authenticated or resolved user_id.")
    return user_id


async def calculate_position_size(
    entry_price: float,
    stop_price: float,
    account_equity: Optional[float] = None,
    risk_percent: Optional[float] = None,
    risk_amount: Optional[float] = None,
    side: str = "long",
    leverage: Optional[float] = None,
    fee_bps: float = 0.0,
) -> Dict[str, Any]:
    """Calculate deterministic position size from account risk and stop distance."""
    entry = float(entry_price)
    stop = float(stop_price)
    if entry <= 0 or stop <= 0:
        raise ValueError("entry_price and stop_price must be greater than zero.")
    if entry == stop:
        raise ValueError("entry_price and stop_price must be different.")

    normalized_side = str(side or "long").strip().lower()
    if normalized_side not in {"long", "short", "buy", "sell"}:
        raise ValueError("side must be one of: long, short, buy, sell.")

    if risk_amount is None and risk_percent is None:
        raise ValueError("Provide risk_amount or risk_percent.")
    if risk_percent is not None and account_equity is None and risk_amount is None:
        raise ValueError("account_equity is required when only risk_percent is provided.")

    resolved_risk_amount = float(risk_amount) if risk_amount is not None else (
        float(account_equity) * (float(risk_percent) / 100.0)
    )
    if resolved_risk_amount <= 0:
        raise ValueError("Resolved risk amount must be greater than zero.")

    stop_distance = abs(entry - stop)
    stop_distance_percent = (stop_distance / entry) * 100.0
    position_size_units = resolved_risk_amount / stop_distance
    position_notional = position_size_units * entry
    resolved_leverage = max(float(leverage or 1.0), 1.0)
    estimated_margin_required = position_notional / resolved_leverage
    estimated_round_trip_fees = position_notional * (float(fee_bps or 0.0) / 10_000.0) * 2.0
    estimated_total_loss_at_stop = resolved_risk_amount + estimated_round_trip_fees

    warnings: List[str] = []
    if normalized_side in {"long", "buy"} and stop >= entry:
        warnings.append("Long sizing usually expects stop_price below entry_price.")
    if normalized_side in {"short", "sell"} and stop <= entry:
        warnings.append("Short sizing usually expects stop_price above entry_price.")
    if account_equity is not None and estimated_margin_required > float(account_equity):
        warnings.append("Estimated margin required exceeds provided account_equity.")
    if resolved_leverage > 1 and position_notional > resolved_risk_amount * 100:
        warnings.append("Large notional relative to risk budget; double-check liquidity and slippage.")

    return {
        "classification": "position_sizing",
        "side": normalized_side,
        "entry_price": entry,
        "stop_price": stop,
        "risk_amount": round(resolved_risk_amount, 8),
        "risk_percent": (
            round((resolved_risk_amount / float(account_equity)) * 100.0, 4)
            if account_equity not in {None, 0}
            else (_float_or_none(risk_percent))
        ),
        "stop_distance": round(stop_distance, 8),
        "stop_distance_percent": round(stop_distance_percent, 4),
        "position_size_units": round(position_size_units, 8),
        "position_notional": round(position_notional, 8),
        "estimated_margin_required": round(estimated_margin_required, 8),
        "estimated_round_trip_fees": round(estimated_round_trip_fees, 8),
        "estimated_total_loss_at_stop": round(estimated_total_loss_at_stop, 8),
        "leverage": resolved_leverage,
        "warnings": warnings,
    }


async def scan_markets(
    category: Optional[str] = None,
    symbols_csv: Optional[str] = None,
    limit: int = 5,
    sort_by: str = "score",
    directional_bias: str = "either",
    min_volume_24h: Optional[float] = None,
    min_abs_change_24h: Optional[float] = None,
) -> Dict[str, Any]:
    """Build a lightweight ranked market scan from tracked backend assets."""
    from main import market_handler

    normalized_category = normalize_category(category) if category else None
    normalized_sort = str(sort_by or "score").strip().lower()
    normalized_bias = str(directional_bias or "either").strip().lower()
    if normalized_sort not in {"score", "volume_24h", "change_24h", "open_interest"}:
        raise ValueError("sort_by must be one of: score, volume_24h, change_24h, open_interest.")
    if normalized_bias not in {"either", "bullish", "bearish"}:
        raise ValueError("directional_bias must be one of: either, bullish, bearish.")

    requested_symbols = [
        item.strip().upper()
        for item in str(symbols_csv or "").split(",")
        if item.strip()
    ]
    market_context = get_current_market_context() or {}
    context_watchlist = [
        str(item).strip().upper()
        for item in market_context.get("watchlist_symbols", [])
        if str(item).strip()
    ]
    universe = requested_symbols or context_watchlist or [str(item).upper() for item in settings.TRADING_ASSETS]

    service = get_market_service()
    ranked: List[Dict[str, Any]] = []
    for symbol in universe:
        try:
            coin_info = await service.get_coin_info(symbol)
            price_update = market_handler.get_price(symbol)
            if not coin_info or not price_update:
                continue

            categories = coin_info.categories or []
            if normalized_category and normalized_category not in categories:
                continue

            change_24h = float(price_update.change_24h or 0.0)
            if normalized_bias == "bullish" and change_24h < 0:
                continue
            if normalized_bias == "bearish" and change_24h > 0:
                continue

            volume_24h = float(price_update.volume_24h or 0.0)
            open_interest = float(price_update.open_interest or 0.0)
            abs_change = abs(change_24h)
            if min_volume_24h is not None and volume_24h < float(min_volume_24h):
                continue
            if min_abs_change_24h is not None and abs_change < float(min_abs_change_24h):
                continue

            score = (volume_24h / 1_000_000.0) + (abs_change * 10.0) + (open_interest / 1_000_000.0)
            reasons = []
            if volume_24h > 0:
                reasons.append("active 24h volume")
            if abs_change >= 5:
                reasons.append("strong 24h move")
            elif abs_change >= 2:
                reasons.append("meaningful 24h move")
            if open_interest > 0:
                reasons.append("derivatives interest visible")
            if normalized_category and normalized_category in categories:
                reasons.append(f"{normalized_category} match")

            ranked.append(
                {
                    "symbol": str(symbol).upper(),
                    "name": coin_info.name,
                    "price": price_update.price,
                    "change_24h": price_update.change_24h,
                    "volume_24h": price_update.volume_24h,
                    "open_interest": price_update.open_interest,
                    "funding_rate": price_update.funding_rate,
                    "categories": categories,
                    "score": round(score, 4),
                    "reasons": reasons[:3],
                }
            )
        except Exception:
            continue

    if normalized_sort == "score":
        ranked.sort(key=lambda item: (-float(item["score"]), item["symbol"]))
    elif normalized_sort == "volume_24h":
        ranked.sort(key=lambda item: (-float(item["volume_24h"] or 0.0), item["symbol"]))
    elif normalized_sort == "open_interest":
        ranked.sort(key=lambda item: (-float(item["open_interest"] or 0.0), item["symbol"]))
    else:
        ranked.sort(key=lambda item: (-abs(float(item["change_24h"] or 0.0)), item["symbol"]))

    limited = ranked[: max(0, int(limit or 0))]
    for idx, item in enumerate(limited, start=1):
        item["rank"] = idx

    return {
        "classification": "market_scan",
        "universe_size": len(universe),
        "matched": len(ranked),
        "sort_by": normalized_sort,
        "directional_bias": normalized_bias,
        "category": normalized_category,
        "assets": limited,
    }


async def create_trade_debrief(
    summary: str,
    exchange: Optional[str] = None,
    symbol: Optional[str] = None,
    side: Optional[str] = None,
    entry_price: Optional[float] = None,
    exit_price: Optional[float] = None,
    pnl: Optional[float] = None,
    tags_csv: Optional[str] = None,
    lesson: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Persist one structured trade debrief entry for the active user."""
    user_id = _require_user_id()
    tags = [
        item.strip()
        for item in str(tags_csv or "").split(",")
        if item.strip()
    ]
    record = get_trade_debrief_service().create_entry(
        user_id=user_id,
        summary=summary,
        exchange=exchange,
        symbol=symbol,
        side=side,
        entry_price=entry_price,
        exit_price=exit_price,
        pnl=pnl,
        lesson=lesson,
        notes=notes,
        tags=tags,
    )
    recent_entries = get_trade_debrief_service().list_entries(user_id=user_id, limit=5)
    return {
        "classification": "journal_debrief",
        "entry": record,
        "recent_entry_count": len(recent_entries),
    }


def register_decision_support_tools() -> None:
    """Register decision-support tools."""
    tool_registry.register(
        ToolDefinition(
            name="calculate_position_size",
            description=(
                "Calculate deterministic position size from entry, stop, and risk budget. "
                "Use for capital allocation, stop-based sizing, and fast risk review."
            ),
            parameters=[
                ToolParameter(name="entry_price", type="number", description="Planned entry price", required=True),
                ToolParameter(name="stop_price", type="number", description="Invalidation or stop-loss price", required=True),
                ToolParameter(name="account_equity", type="number", description="Optional account equity used for risk_percent conversion", required=False),
                ToolParameter(name="risk_percent", type="number", description="Optional account risk percent such as 1 or 0.5", required=False),
                ToolParameter(name="risk_amount", type="number", description="Optional direct risk amount in quote currency", required=False),
                ToolParameter(name="side", type="string", description="Trade side: long, short, buy, or sell", required=False),
                ToolParameter(name="leverage", type="number", description="Optional leverage used to estimate margin required", required=False),
                ToolParameter(name="fee_bps", type="number", description="Optional estimated fee rate in basis points per side", required=False),
            ],
            function=calculate_position_size,
        )
    )
    tool_registry.register(
        ToolDefinition(
            name="scan_markets",
            description=(
                "Run a lightweight ranked scan over the tracked asset universe using current market data, "
                "category filters, and simple ranking signals such as volume, 24h move, and open interest."
            ),
            parameters=[
                ToolParameter(name="category", type="string", description="Optional normalized category filter such as DeFi or Layer 1", required=False),
                ToolParameter(name="symbols_csv", type="string", description="Optional comma-separated symbols to scan instead of the default tracked universe", required=False),
                ToolParameter(name="limit", type="number", description="Maximum number of ranked assets to return", required=False),
                ToolParameter(name="sort_by", type="string", description="Ranking field: score, volume_24h, change_24h, or open_interest", required=False),
                ToolParameter(name="directional_bias", type="string", description="Filter direction: either, bullish, or bearish", required=False),
                ToolParameter(name="min_volume_24h", type="number", description="Optional minimum 24h volume filter", required=False),
                ToolParameter(name="min_abs_change_24h", type="number", description="Optional minimum absolute 24h move filter", required=False),
            ],
            function=scan_markets,
        )
    )
    tool_registry.register(
        ToolDefinition(
            name="create_trade_debrief",
            description=(
                "Save one structured post-trade debrief entry for the active user. "
                "Use it to store the trade summary, lesson, tags, and optional entry/exit/PnL details."
            ),
            parameters=[
                ToolParameter(name="summary", type="string", description="Short trade recap or debrief summary", required=True),
                ToolParameter(name="exchange", type="string", description="Optional market venue such as phantom, spot, or futures", required=False),
                ToolParameter(name="symbol", type="string", description="Optional asset or market symbol", required=False),
                ToolParameter(name="side", type="string", description="Optional side such as long or short", required=False),
                ToolParameter(name="entry_price", type="number", description="Optional entry price", required=False),
                ToolParameter(name="exit_price", type="number", description="Optional exit price", required=False),
                ToolParameter(name="pnl", type="number", description="Optional realized PnL if already known", required=False),
                ToolParameter(name="tags_csv", type="string", description="Optional comma-separated mistake or lesson tags", required=False),
                ToolParameter(name="lesson", type="string", description="Optional key lesson learned", required=False),
                ToolParameter(name="notes", type="string", description="Optional longer notes", required=False),
            ],
            function=create_trade_debrief,
        )
    )


__all__ = [
    "calculate_position_size",
    "scan_markets",
    "create_trade_debrief",
    "register_decision_support_tools",
]
