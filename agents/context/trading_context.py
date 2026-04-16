"""
Trading Context Management

This module manages the current trading context for the agent, including:
- Current exchange (drift or backpack)
- Current asset being traded
- Trading mode (asset-locked or global)
"""

from typing import Optional, Literal
from dataclasses import dataclass
from datetime import datetime


ExchangeType = Literal["drift", "backpack"]
TradingMode = Literal["asset_locked", "global"]


@dataclass
class TradingContext:
    """
    Trading context information for the agent
    
    Attributes:
        exchange: Current exchange (drift or backpack)
        asset: Current asset symbol (e.g., BTC, ETH, SOL)
        mode: Trading mode (asset_locked or global)
        updated_at: Last update timestamp
    """
    exchange: ExchangeType
    asset: Optional[str] = None
    mode: TradingMode = "global"
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "exchange": self.exchange,
            "asset": self.asset,
            "mode": self.mode,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_context_summary(self) -> str:
        """Get human-readable context summary"""
        if self.mode == "asset_locked" and self.asset:
            return f"Trading {self.asset} on {self.exchange.upper()} (Asset-Locked Mode)"
        else:
            return f"Trading on {self.exchange.upper()} (Global Mode - All Assets)"


# Global context instance (singleton pattern)
_current_context: Optional[TradingContext] = None


def get_trading_context() -> Optional[TradingContext]:
    """
    Get current trading context
    
    Returns:
        Current TradingContext or None if not set
    """
    return _current_context


def set_trading_context(
    exchange: ExchangeType,
    asset: Optional[str] = None,
    mode: TradingMode = "global"
) -> TradingContext:
    """
    Set trading context
    
    Args:
        exchange: Exchange to use (drift or backpack)
        asset: Asset symbol (required for asset_locked mode)
        mode: Trading mode (asset_locked or global)
    
    Returns:
        Updated TradingContext
    
    Raises:
        ValueError: If asset is None in asset_locked mode
    """
    global _current_context
    
    # Validate
    if mode == "asset_locked" and not asset:
        raise ValueError("Asset is required for asset_locked mode")
    
    # Normalize asset to uppercase
    if asset:
        asset = asset.upper()
    
    _current_context = TradingContext(
        exchange=exchange,
        asset=asset,
        mode=mode,
        updated_at=datetime.now()
    )
    
    return _current_context


def update_exchange(exchange: ExchangeType) -> TradingContext:
    """
    Update only the exchange in current context
    
    Args:
        exchange: New exchange (drift or backpack)
    
    Returns:
        Updated TradingContext
    """
    global _current_context
    
    if _current_context is None:
        # Create new context with default values
        _current_context = TradingContext(exchange=exchange)
    else:
        _current_context.exchange = exchange
        _current_context.updated_at = datetime.now()
    
    return _current_context


def update_asset(asset: Optional[str]) -> TradingContext:
    """
    Update only the asset in current context
    
    Args:
        asset: New asset symbol or None
    
    Returns:
        Updated TradingContext
    """
    global _current_context
    
    if _current_context is None:
        # Create new context with default exchange
        _current_context = TradingContext(exchange="drift", asset=asset)
    else:
        _current_context.asset = asset.upper() if asset else None
        _current_context.updated_at = datetime.now()
    
    return _current_context


def update_mode(mode: TradingMode) -> TradingContext:
    """
    Update only the trading mode in current context
    
    Args:
        mode: New trading mode (asset_locked or global)
    
    Returns:
        Updated TradingContext
    
    Raises:
        ValueError: If switching to asset_locked mode without asset
    """
    global _current_context
    
    if mode == "asset_locked" and (_current_context is None or not _current_context.asset):
        raise ValueError("Cannot switch to asset_locked mode without setting an asset first")
    
    if _current_context is None:
        # Create new context with default values
        _current_context = TradingContext(exchange="drift", mode=mode)
    else:
        _current_context.mode = mode
        _current_context.updated_at = datetime.now()
    
    return _current_context


def clear_trading_context():
    """Clear current trading context"""
    global _current_context
    _current_context = None


def get_context_for_agent() -> str:
    """
    Get formatted context string for agent system prompt
    
    Returns:
        Formatted context string describing current trading state
    """
    context = get_trading_context()
    
    if context is None:
        return "No trading context set. Please set exchange and asset before trading."
    
    lines = [
        "=== CURRENT TRADING CONTEXT ===",
        f"Exchange: {context.exchange.upper()}",
        f"Mode: {context.mode.replace('_', ' ').title()}",
    ]
    
    if context.asset:
        lines.append(f"Asset: {context.asset}")
    else:
        lines.append("Asset: All assets available (Global Mode)")
    
    if context.updated_at:
        lines.append(f"Last Updated: {context.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
    
    lines.append("=" * 31)
    
    return "\n".join(lines)
