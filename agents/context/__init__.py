"""
Agent Context Module

This module provides context management for trading agents.
Context includes current exchange, asset, and trading mode.

Usage:
    from agents.context import (
        get_trading_context,
        set_trading_context,
        update_exchange,
        update_asset,
        update_mode,
        get_context_for_agent
    )
    
    # Set full context
    context = set_trading_context(
        exchange="drift",
        asset="BTC",
        mode="asset_locked"
    )
    
    # Update only exchange
    context = update_exchange("backpack")
    
    # Get context for agent prompt
    context_str = get_context_for_agent()
"""

from .trading_context import (
    TradingContext,
    ExchangeType,
    TradingMode,
    get_trading_context,
    set_trading_context,
    update_exchange,
    update_asset,
    update_mode,
    clear_trading_context,
    get_context_for_agent
)

__all__ = [
    "TradingContext",
    "ExchangeType",
    "TradingMode",
    "get_trading_context",
    "set_trading_context",
    "update_exchange",
    "update_asset",
    "update_mode",
    "clear_trading_context",
    "get_context_for_agent"
]
