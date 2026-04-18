"""Backpack account, history, and execution tools."""
from __future__ import annotations

from typing import Any, Dict, Optional

from agents.backpack_execution import is_backpack_execution_allowed
from agents.backpack_execution.client import BackpackClient, get_backpack_client
from agents.exchange_connections import get_exchange_connection_service
from agents.tools import ToolDefinition, ToolParameter, tool_registry
from agents.tools.core.runtime_context import (
    get_current_backpack_execution,
    get_current_user_id,
)


def _get_client(*, require_live_execution: bool = False) -> BackpackClient:
    """Return Backpack client from user connection store or env fallback."""
    user_id = get_current_user_id()
    if user_id:
        credentials = get_exchange_connection_service().get_active_credentials(
            user_id=user_id,
            exchange="backpack",
            require_trading_enabled=require_live_execution,
        )
        if not credentials:
            raise ValueError(
                f"No active Backpack connection is configured for user '{user_id}'."
            )
        return BackpackClient(
            api_key=credentials["api_key"],
            api_secret=credentials["api_secret"],
        )

    client = get_backpack_client()
    client.ensure_credentials()
    return client


def _get_execution_context() -> Dict[str, Any]:
    """Return normalized Backpack execution context from runtime."""
    return get_current_backpack_execution() or {"enabled": False, "exchange": "backpack"}


def _require_live_execution_enabled() -> Dict[str, Any]:
    """Raise if live Backpack execution is not allowed in this request."""
    context = _get_execution_context()
    if str(context.get("exchange", "backpack")).strip().lower() != "backpack":
        raise ValueError("Backpack execution context is not active for this request.")
    if not is_backpack_execution_allowed(context):
        raise ValueError(
            "Backpack live execution is disabled for this request or by backend configuration."
        )
    return context


async def backpack_get_balances() -> Dict[str, Any]:
    """Return Backpack balances."""
    data = await _get_client().get_balances()
    return {"exchange": "backpack", "data": data}


async def backpack_get_collateral(subaccount_id: Optional[int] = None) -> Dict[str, Any]:
    """Return Backpack collateral summary."""
    data = await _get_client().get_collateral(subaccount_id=subaccount_id)
    return {"exchange": "backpack", "data": data}


async def backpack_get_open_orders(
    symbol: Optional[str] = None,
    market_type: Optional[str] = None,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """Return Backpack open orders."""
    data = await _get_client().get_open_orders(
        symbol=symbol,
        market_type=market_type,
        limit=limit,
    )
    return {"exchange": "backpack", "data": data}


async def backpack_get_order_history(
    symbol: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Dict[str, Any]:
    """Return Backpack historical orders."""
    data = await _get_client().get_order_history(
        symbol=symbol,
        limit=limit,
        offset=offset,
    )
    return {"exchange": "backpack", "data": data}


async def backpack_get_fill_history(
    symbol: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Dict[str, Any]:
    """Return Backpack historical fills."""
    data = await _get_client().get_fill_history(
        symbol=symbol,
        limit=limit,
        offset=offset,
    )
    return {"exchange": "backpack", "data": data}


async def backpack_get_positions(
    symbol: Optional[str] = None,
    market_type: Optional[str] = None,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """Return Backpack current positions."""
    data = await _get_client().get_positions(
        symbol=symbol,
        market_type=market_type,
        limit=limit,
    )
    return {"exchange": "backpack", "data": data}


async def backpack_get_position_history(
    symbol: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Dict[str, Any]:
    """Return Backpack historical positions."""
    data = await _get_client().get_position_history(
        symbol=symbol,
        limit=limit,
        offset=offset,
    )
    return {"exchange": "backpack", "data": data}


async def backpack_place_order(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str] = None,
    time_in_force: Optional[str] = None,
    post_only: Optional[bool] = None,
    reduce_only: Optional[bool] = None,
    client_id: Optional[str] = None,
    self_trade_prevention: Optional[str] = None,
) -> Dict[str, Any]:
    """Place one Backpack live order when the request-level gate allows it."""
    _require_live_execution_enabled()
    data = await _get_client(require_live_execution=True).place_order(
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        time_in_force=time_in_force,
        post_only=post_only,
        reduce_only=reduce_only,
        client_id=client_id,
        self_trade_prevention=self_trade_prevention,
    )
    return {
        "exchange": "backpack",
        "execution_enabled": True,
        "data": data,
    }


async def backpack_cancel_order(
    order_id: Optional[str] = None,
    client_id: Optional[str] = None,
    symbol: Optional[str] = None,
) -> Dict[str, Any]:
    """Cancel one Backpack live order when the request-level gate allows it."""
    if not order_id and not client_id:
        raise ValueError("Provide order_id or client_id to cancel a Backpack order.")

    _require_live_execution_enabled()
    data = await _get_client(require_live_execution=True).cancel_order(
        order_id=order_id,
        client_id=client_id,
        symbol=symbol,
    )
    return {
        "exchange": "backpack",
        "execution_enabled": True,
        "data": data,
    }


def register_backpack_execution_tools() -> None:
    """Register Backpack account, history, and execution tools."""
    tool_registry.register(
        ToolDefinition(
            name="backpack_get_balances",
            description="Get Backpack account balances and locked funds using authenticated private API access.",
            parameters=[],
            function=backpack_get_balances,
        )
    )
    tool_registry.register(
        ToolDefinition(
            name="backpack_get_collateral",
            description="Get Backpack collateral summary for the connected account or subaccount.",
            parameters=[
                ToolParameter(
                    name="subaccount_id",
                    type="number",
                    description="Optional Backpack subaccount ID",
                    required=False,
                )
            ],
            function=backpack_get_collateral,
        )
    )
    tool_registry.register(
        ToolDefinition(
            name="backpack_get_open_orders",
            description="Get currently open Backpack orders for the connected account.",
            parameters=[
                ToolParameter(
                    name="symbol",
                    type="string",
                    description="Optional symbol such as BTC_USDC or SOL_USDC",
                    required=False,
                ),
                ToolParameter(
                    name="market_type",
                    type="string",
                    description="Optional Backpack market type filter",
                    required=False,
                ),
                ToolParameter(
                    name="limit",
                    type="number",
                    description="Optional result limit",
                    required=False,
                ),
            ],
            function=backpack_get_open_orders,
        )
    )
    tool_registry.register(
        ToolDefinition(
            name="backpack_get_order_history",
            description="Get Backpack historical order records for the connected account.",
            parameters=[
                ToolParameter(
                    name="symbol",
                    type="string",
                    description="Optional symbol such as BTC_USDC or SOL_USDC",
                    required=False,
                ),
                ToolParameter(
                    name="limit",
                    type="number",
                    description="Optional result limit",
                    required=False,
                ),
                ToolParameter(
                    name="offset",
                    type="number",
                    description="Optional pagination offset",
                    required=False,
                ),
            ],
            function=backpack_get_order_history,
        )
    )
    tool_registry.register(
        ToolDefinition(
            name="backpack_get_fill_history",
            description="Get Backpack fill history for the connected account.",
            parameters=[
                ToolParameter(
                    name="symbol",
                    type="string",
                    description="Optional symbol such as BTC_USDC or SOL_USDC",
                    required=False,
                ),
                ToolParameter(
                    name="limit",
                    type="number",
                    description="Optional result limit",
                    required=False,
                ),
                ToolParameter(
                    name="offset",
                    type="number",
                    description="Optional pagination offset",
                    required=False,
                ),
            ],
            function=backpack_get_fill_history,
        )
    )
    tool_registry.register(
        ToolDefinition(
            name="backpack_get_positions",
            description="Get current Backpack positions for the connected account.",
            parameters=[
                ToolParameter(
                    name="symbol",
                    type="string",
                    description="Optional symbol such as BTC_USDC or SOL_USDC",
                    required=False,
                ),
                ToolParameter(
                    name="market_type",
                    type="string",
                    description="Optional Backpack market type filter",
                    required=False,
                ),
                ToolParameter(
                    name="limit",
                    type="number",
                    description="Optional result limit",
                    required=False,
                ),
            ],
            function=backpack_get_positions,
        )
    )
    tool_registry.register(
        ToolDefinition(
            name="backpack_get_position_history",
            description="Get Backpack historical position snapshots for the connected account.",
            parameters=[
                ToolParameter(
                    name="symbol",
                    type="string",
                    description="Optional symbol such as BTC_USDC or SOL_USDC",
                    required=False,
                ),
                ToolParameter(
                    name="limit",
                    type="number",
                    description="Optional result limit",
                    required=False,
                ),
                ToolParameter(
                    name="offset",
                    type="number",
                    description="Optional pagination offset",
                    required=False,
                ),
            ],
            function=backpack_get_position_history,
        )
    )
    tool_registry.register(
        ToolDefinition(
            name="backpack_place_order",
            description="Place one live Backpack order. This only works when Backpack execution is enabled by both backend config and frontend request gate.",
            parameters=[
                ToolParameter(
                    name="symbol",
                    type="string",
                    description="Backpack symbol such as BTC_USDC or SOL_USDC",
                    required=True,
                ),
                ToolParameter(
                    name="side",
                    type="string",
                    description="Order side such as Bid/Ask or Buy/Sell depending on Backpack API configuration",
                    required=True,
                ),
                ToolParameter(
                    name="order_type",
                    type="string",
                    description="Order type such as Limit, Market, StopLimit, or StopMarket",
                    required=True,
                ),
                ToolParameter(
                    name="quantity",
                    type="string",
                    description="Order quantity as a string to preserve precision",
                    required=True,
                ),
                ToolParameter(
                    name="price",
                    type="string",
                    description="Optional price for limit-style orders",
                    required=False,
                ),
                ToolParameter(
                    name="time_in_force",
                    type="string",
                    description="Optional time in force such as GTC, IOC, or FOK",
                    required=False,
                ),
                ToolParameter(
                    name="post_only",
                    type="boolean",
                    description="Optional post-only flag",
                    required=False,
                ),
                ToolParameter(
                    name="reduce_only",
                    type="boolean",
                    description="Optional reduce-only flag",
                    required=False,
                ),
                ToolParameter(
                    name="client_id",
                    type="string",
                    description="Optional client order ID",
                    required=False,
                ),
                ToolParameter(
                    name="self_trade_prevention",
                    type="string",
                    description="Optional self-trade prevention mode",
                    required=False,
                ),
            ],
            function=backpack_place_order,
        )
    )
    tool_registry.register(
        ToolDefinition(
            name="backpack_cancel_order",
            description="Cancel one live Backpack order. This only works when Backpack execution is enabled by both backend config and frontend request gate.",
            parameters=[
                ToolParameter(
                    name="order_id",
                    type="string",
                    description="Optional Backpack order ID",
                    required=False,
                ),
                ToolParameter(
                    name="client_id",
                    type="string",
                    description="Optional client order ID",
                    required=False,
                ),
                ToolParameter(
                    name="symbol",
                    type="string",
                    description="Optional symbol such as BTC_USDC or SOL_USDC",
                    required=False,
                ),
            ],
            function=backpack_cancel_order,
        )
    )


__all__ = [
    "backpack_get_balances",
    "backpack_get_collateral",
    "backpack_get_open_orders",
    "backpack_get_order_history",
    "backpack_get_fill_history",
    "backpack_get_positions",
    "backpack_get_position_history",
    "backpack_place_order",
    "backpack_cancel_order",
    "register_backpack_execution_tools",
]
