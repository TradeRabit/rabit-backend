"""Drift same-wallet execution preparation tools."""
from __future__ import annotations

from typing import Any, Dict, Optional

from agents.drift_execution import (
    build_drift_execution_wallet_status,
    get_drift_execution_request_service,
    get_drift_execution_tx_builder,
    is_drift_execution_allowed,
    wallet_address_from_user_id,
)
from agents.tools import ToolDefinition, ToolParameter, tool_registry
from agents.tools.core.runtime_context import (
    get_current_drift_execution,
    get_current_user_id,
)


def _require_live_execution_context() -> tuple[str, str, dict]:
    """Require an authenticated same-wallet Drift execution context."""
    user_id = get_current_user_id()
    wallet_address = wallet_address_from_user_id(user_id)
    if not user_id or not wallet_address:
        raise ValueError("Drift execution tools require an authenticated wallet user.")

    drift_execution = get_current_drift_execution() or {"enabled": False, "exchange": "drift"}
    if str(drift_execution.get("exchange", "drift")).strip().lower() != "drift":
        raise ValueError("Drift execution context is not active for this request.")
    if not is_drift_execution_allowed(drift_execution):
        raise ValueError(
            "Drift live execution is disabled for this request or by backend configuration."
        )

    execution_wallet = build_drift_execution_wallet_status(user_id)
    if not execution_wallet.get("verified") or execution_wallet.get("mode") != "same_wallet":
        raise ValueError("Only verified same-wallet Drift execution is supported in v1.")
    return user_id, wallet_address, execution_wallet


async def drift_place_order(
    side: str,
    order_type: str,
    base_asset_amount: str,
    market_index: Optional[int] = None,
    symbol: Optional[str] = None,
    price: Optional[str] = None,
    sub_account_id: int = 0,
    reduce_only: bool = False,
    post_only: bool = False,
    immediate_or_cancel: bool = False,
    client_order_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Prepare a same-wallet Drift place-order payload for client signing."""
    user_id, wallet_address, execution_wallet = _require_live_execution_context()
    order_intent = {
        "market_type": "perp",
        "market_index": market_index,
        "symbol": symbol,
        "side": str(side).strip().lower(),
        "order_type": str(order_type).strip().lower(),
        "base_asset_amount": base_asset_amount,
        "price": price,
        "reduce_only": reduce_only,
        "post_only": post_only,
        "immediate_or_cancel": immediate_or_cancel,
        "client_order_id": client_order_id,
    }
    prepared_transaction = await get_drift_execution_tx_builder().build_place_perp_order_payload(
        wallet_address=wallet_address,
        sub_account_id=sub_account_id,
        order_intent=order_intent,
    )
    record = get_drift_execution_request_service().create_prepared_request(
        user_id=user_id,
        auth_wallet_address=wallet_address,
        execution_wallet_status=execution_wallet,
        sub_account_id=sub_account_id,
        order_intent=order_intent,
        prepared_transaction=prepared_transaction,
    )
    return {
        "exchange": "drift",
        "execution_enabled": True,
        "execution_id": record["execution_id"],
        "status": record["status"],
        "mode": record["mode"],
        "requires_client_signature": True,
        "data": record,
    }


async def drift_cancel_order(
    order_id: Optional[str] = None,
    user_order_id: Optional[int] = None,
    sub_account_id: int = 0,
) -> Dict[str, Any]:
    """Prepare a same-wallet Drift cancel-order payload for client signing."""
    user_id, wallet_address, execution_wallet = _require_live_execution_context()
    if order_id is None and user_order_id is None:
        raise ValueError("Provide order_id or user_order_id to cancel a Drift order.")

    order_intent = {
        "action": "cancel_order",
        "market_type": "perp",
        "order_id": order_id,
        "user_order_id": user_order_id,
    }
    prepared_transaction = await get_drift_execution_tx_builder().build_cancel_order_payload(
        wallet_address=wallet_address,
        sub_account_id=sub_account_id,
        order_id=order_id,
        user_order_id=user_order_id,
    )
    record = get_drift_execution_request_service().create_prepared_request(
        user_id=user_id,
        auth_wallet_address=wallet_address,
        execution_wallet_status=execution_wallet,
        sub_account_id=sub_account_id,
        order_intent=order_intent,
        prepared_transaction=prepared_transaction,
    )
    return {
        "exchange": "drift",
        "execution_enabled": True,
        "execution_id": record["execution_id"],
        "status": record["status"],
        "mode": record["mode"],
        "requires_client_signature": True,
        "data": record,
    }


def register_drift_execution_tools() -> None:
    """Register same-wallet Drift execution-preparation tools."""
    tool_registry.register(
        ToolDefinition(
            name="drift_place_order",
            description=(
                "Prepare a same-wallet Drift perp order for live execution. "
                "This builds an unsigned transaction payload and execution request record for mobile wallet signing. "
                "It only works when Drift execution is enabled by backend config and request gate."
            ),
            parameters=[
                ToolParameter(name="side", type="string", description="Order side: long, short, buy, or sell", required=True),
                ToolParameter(name="order_type", type="string", description="Order type: limit, market, trigger_limit, or trigger_market", required=True),
                ToolParameter(name="base_asset_amount", type="string", description="Base asset amount as an integer-like string", required=True),
                ToolParameter(name="market_index", type="number", description="Required Drift market index for v1 transaction building", required=False),
                ToolParameter(name="symbol", type="string", description="Optional market symbol such as SOL-PERP", required=False),
                ToolParameter(name="price", type="string", description="Required for limit-style orders", required=False),
                ToolParameter(name="sub_account_id", type="number", description="Drift subaccount index. Defaults to 0.", required=False),
                ToolParameter(name="reduce_only", type="boolean", description="Optional reduce-only flag", required=False),
                ToolParameter(name="post_only", type="boolean", description="Optional post-only flag", required=False),
                ToolParameter(name="immediate_or_cancel", type="boolean", description="Optional IOC flag", required=False),
                ToolParameter(name="client_order_id", type="number", description="Optional client order ID", required=False),
            ],
            function=drift_place_order,
        )
    )
    tool_registry.register(
        ToolDefinition(
            name="drift_cancel_order",
            description=(
                "Prepare a same-wallet Drift cancel-order transaction for live execution. "
                "This builds an unsigned transaction payload and execution request record for mobile wallet signing. "
                "It only works when Drift execution is enabled by backend config and request gate."
            ),
            parameters=[
                ToolParameter(name="order_id", type="string", description="Optional Drift order ID", required=False),
                ToolParameter(name="user_order_id", type="number", description="Optional Drift user order ID", required=False),
                ToolParameter(name="sub_account_id", type="number", description="Drift subaccount index. Defaults to 0.", required=False),
            ],
            function=drift_cancel_order,
        )
    )


__all__ = [
    "drift_place_order",
    "drift_cancel_order",
    "register_drift_execution_tools",
]
