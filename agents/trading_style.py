"""Trading style helpers for agent market-analysis behavior."""
from typing import Final


TRADING_STYLE_BALANCED: Final[str] = "balanced"
TRADING_STYLE_PRICE_ACTION: Final[str] = "price_action"
TRADING_STYLE_TREND_FOLLOWING: Final[str] = "trend_following"
TRADING_STYLE_MOMENTUM_BREAKOUT: Final[str] = "momentum_breakout"
TRADING_STYLE_MEAN_REVERSION: Final[str] = "mean_reversion"
TRADING_STYLE_SMART_MONEY: Final[str] = "smart_money"
TRADING_STYLE_RISK_FIRST: Final[str] = "risk_first"
TRADING_STYLE_SYSTEMATIC: Final[str] = "systematic"

VALID_TRADING_STYLES: Final[set[str]] = {
    TRADING_STYLE_BALANCED,
    TRADING_STYLE_PRICE_ACTION,
    TRADING_STYLE_TREND_FOLLOWING,
    TRADING_STYLE_MOMENTUM_BREAKOUT,
    TRADING_STYLE_MEAN_REVERSION,
    TRADING_STYLE_SMART_MONEY,
    TRADING_STYLE_RISK_FIRST,
    TRADING_STYLE_SYSTEMATIC,
}


def normalize_trading_style(value: str | None) -> str:
    """Normalize a frontend trading style value to a supported style."""
    normalized = str(value or TRADING_STYLE_BALANCED).strip().lower()
    if normalized in VALID_TRADING_STYLES:
        return normalized
    return TRADING_STYLE_BALANCED


def get_trading_style_guidance(style: str) -> str:
    """Return system-prompt guidance for the selected trading style."""
    normalized = normalize_trading_style(style)
    mapping = {
        TRADING_STYLE_BALANCED: (
            "Use a balanced market style. Combine price action, supporting indicators, "
            "risk framing, and context without overcommitting to a single lens."
        ),
        TRADING_STYLE_PRICE_ACTION: (
            "Prefer price action reading first. Focus on structure, support and resistance, "
            "swing highs and lows, candle behavior, and market context before indicators."
        ),
        TRADING_STYLE_TREND_FOLLOWING: (
            "Prefer trend-following logic. Emphasize directional bias, continuation setups, "
            "trend confirmation, and pullback entries over reversal hunting."
        ),
        TRADING_STYLE_MOMENTUM_BREAKOUT: (
            "Prefer momentum and breakout logic. Focus on expansion, breakout confirmation, "
            "volume or momentum support, and invalidation if the breakout fails."
        ),
        TRADING_STYLE_MEAN_REVERSION: (
            "Prefer mean-reversion logic. Focus on stretched conditions, reversion zones, "
            "overextension, and the risk that strong trends can keep extending."
        ),
        TRADING_STYLE_SMART_MONEY: (
            "Prefer a smart-money style. Focus on liquidity areas, sweeps, displacement, "
            "order blocks, imbalances, and market structure shifts when relevant."
        ),
        TRADING_STYLE_RISK_FIRST: (
            "Prefer a risk-first style. Lead with invalidation, downside, stop logic, "
            "position quality, and whether the trade is worth taking at all."
        ),
        TRADING_STYLE_SYSTEMATIC: (
            "Prefer a systematic style. Be rule-based, explicit about conditions, and "
            "frame setups as repeatable criteria rather than intuition."
        ),
    }
    return mapping[normalized]
