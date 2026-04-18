"""Drift account-linked read-only context tools.

Classification:
- purpose: account-linked and private-account read-only Drift tools
- scope: authenticated wallet identity, frontend market context, balances, collateral, open orders, positions, and recent account history
- non-goals: public market duplication, live order placement, signer custody, delegated signing
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from agents.drift_execution import (
    build_drift_execution_wallet_status,
    wallet_address_from_user_id,
)
from agents.drift_execution.account_client import get_drift_account_client
from agents.tools import ToolDefinition, ToolParameter, tool_registry
from agents.tools.core.runtime_context import (
    get_current_drift_execution,
    get_current_market_context,
    get_current_user_id,
)


def _require_wallet_address() -> str:
    wallet_address = wallet_address_from_user_id(get_current_user_id())
    if not wallet_address:
        raise ValueError(
            "Drift account read-only tools require an authenticated wallet user."
        )
    return wallet_address


async def drift_get_account_context() -> Dict[str, Any]:
    """Return authenticated wallet-linked Drift request context."""
    user_id = get_current_user_id()
    wallet_address = wallet_address_from_user_id(user_id)
    market_context = get_current_market_context() or {}
    drift_execution = get_current_drift_execution() or {
        "enabled": False,
        "exchange": "drift",
    }
    execution_wallet = build_drift_execution_wallet_status(user_id)

    return {
        "exchange": "drift",
        "classification": "account_linked_read_only_context",
        "user_id": user_id,
        "wallet_address": wallet_address,
        "authenticated_wallet_linked": wallet_address is not None,
        "execution_wallet": execution_wallet,
        "market_context": market_context,
        "drift_execution": drift_execution,
        "private_account_reads_available": True,
        "notes": [
            "This tool exposes authenticated wallet-linked request context.",
            "Private Drift account reads are available through the dedicated balances, collateral, orders, positions, and history tools.",
            "Use this to align Drift analysis with the active wallet identity and frontend market context before calling deeper account tools.",
        ],
    }


async def drift_get_account_snapshot(sub_account_id: int = 0) -> Dict[str, Any]:
    """Return private read-only Drift subaccount snapshot for the authenticated wallet."""
    wallet_address = _require_wallet_address()
    data = await get_drift_account_client().get_account_snapshot(
        wallet_address=wallet_address,
        sub_account_id=sub_account_id,
    )
    return {
        "exchange": "drift",
        "classification": "private_account_read_only",
        "data": data,
    }


async def drift_get_balances(sub_account_id: int = 0) -> Dict[str, Any]:
    """Return private read-only Drift spot balances for the authenticated wallet."""
    wallet_address = _require_wallet_address()
    data = await get_drift_account_client().get_balances(
        wallet_address=wallet_address,
        sub_account_id=sub_account_id,
    )
    return {
        "exchange": "drift",
        "classification": "private_account_read_only",
        "data": data,
    }


async def drift_get_collateral(sub_account_id: int = 0) -> Dict[str, Any]:
    """Return private read-only Drift collateral summary for the authenticated wallet."""
    wallet_address = _require_wallet_address()
    data = await get_drift_account_client().get_collateral(
        wallet_address=wallet_address,
        sub_account_id=sub_account_id,
    )
    return {
        "exchange": "drift",
        "classification": "private_account_read_only",
        "data": data,
    }


async def drift_get_open_orders(sub_account_id: int = 0) -> Dict[str, Any]:
    """Return private read-only Drift open orders for the authenticated wallet."""
    wallet_address = _require_wallet_address()
    data = await get_drift_account_client().get_open_orders(
        wallet_address=wallet_address,
        sub_account_id=sub_account_id,
    )
    return {
        "exchange": "drift",
        "classification": "private_account_read_only",
        "data": data,
    }


async def drift_get_open_positions(sub_account_id: int = 0) -> Dict[str, Any]:
    """Return private read-only Drift open perp positions for the authenticated wallet."""
    wallet_address = _require_wallet_address()
    data = await get_drift_account_client().get_open_positions(
        wallet_address=wallet_address,
        sub_account_id=sub_account_id,
    )
    return {
        "exchange": "drift",
        "classification": "private_account_read_only",
        "data": data,
    }


async def drift_get_positions(sub_account_id: int = 0) -> Dict[str, Any]:
    """Return private read-only Drift current positions for the authenticated wallet."""
    wallet_address = _require_wallet_address()
    data = await get_drift_account_client().get_positions(
        wallet_address=wallet_address,
        sub_account_id=sub_account_id,
    )
    return {
        "exchange": "drift",
        "classification": "private_account_read_only",
        "data": data,
    }


async def drift_get_order_history(
    sub_account_id: int = 0,
    limit: int = 20,
    offset: int = 0,
) -> Dict[str, Any]:
    """Return private read-only Drift recent order history for the authenticated wallet."""
    wallet_address = _require_wallet_address()
    data = await get_drift_account_client().get_order_history(
        wallet_address=wallet_address,
        sub_account_id=sub_account_id,
        limit=limit,
        offset=offset,
    )
    return {
        "exchange": "drift",
        "classification": "private_account_history_read_only",
        "data": data,
    }


async def drift_get_fill_history(
    sub_account_id: int = 0,
    limit: int = 20,
    offset: int = 0,
) -> Dict[str, Any]:
    """Return private read-only Drift recent fill history for the authenticated wallet."""
    wallet_address = _require_wallet_address()
    data = await get_drift_account_client().get_fill_history(
        wallet_address=wallet_address,
        sub_account_id=sub_account_id,
        limit=limit,
        offset=offset,
    )
    return {
        "exchange": "drift",
        "classification": "private_account_history_read_only",
        "data": data,
    }


async def drift_get_position_history(
    sub_account_id: int = 0,
    limit: int = 20,
    offset: int = 0,
) -> Dict[str, Any]:
    """Return private read-only Drift recent position-affecting history for the authenticated wallet."""
    wallet_address = _require_wallet_address()
    data = await get_drift_account_client().get_position_history(
        wallet_address=wallet_address,
        sub_account_id=sub_account_id,
        limit=limit,
        offset=offset,
    )
    return {
        "exchange": "drift",
        "classification": "private_account_history_read_only",
        "data": data,
    }


def register_drift_readonly_tools() -> None:
    """Register account-linked read-only Drift tools."""
    tool_registry.register(
        ToolDefinition(
            name="drift_get_account_context",
            description=(
                "Classification: account-linked read-only Drift context tool. "
                "Return the authenticated wallet-derived identity, frontend market context, and current Drift execution gate "
                "for this request. Use it to align later private Drift account and history reads with the active wallet context."
            ),
            parameters=[],
            function=drift_get_account_context,
        )
    )
    tool_registry.register(
        ToolDefinition(
            name="drift_get_account_snapshot",
            description=(
                "Classification: private read-only Drift account tool. "
                "Get subaccount snapshot for the authenticated wallet including open orders, open positions, "
                "spot balances, collateral, and leverage. Requires optional Drift SDK dependencies."
            ),
            parameters=[
                ToolParameter(
                    name="sub_account_id",
                    type="number",
                    description="Drift subaccount index. Defaults to 0.",
                    required=False,
                )
            ],
            function=drift_get_account_snapshot,
        )
    )
    tool_registry.register(
        ToolDefinition(
            name="drift_get_balances",
            description=(
                "Classification: private read-only Drift account tool. "
                "Get current non-zero spot balances for the authenticated wallet and one Drift subaccount. "
                "Requires optional Drift SDK dependencies."
            ),
            parameters=[
                ToolParameter(
                    name="sub_account_id",
                    type="number",
                    description="Drift subaccount index. Defaults to 0.",
                    required=False,
                )
            ],
            function=drift_get_balances,
        )
    )
    tool_registry.register(
        ToolDefinition(
            name="drift_get_collateral",
            description=(
                "Classification: private read-only Drift account tool. "
                "Get collateral summary, free collateral, and leverage for the authenticated wallet and one Drift subaccount. "
                "Requires optional Drift SDK dependencies."
            ),
            parameters=[
                ToolParameter(
                    name="sub_account_id",
                    type="number",
                    description="Drift subaccount index. Defaults to 0.",
                    required=False,
                )
            ],
            function=drift_get_collateral,
        )
    )
    tool_registry.register(
        ToolDefinition(
            name="drift_get_open_orders",
            description=(
                "Classification: private read-only Drift account tool. "
                "Get open orders for the authenticated wallet and one Drift subaccount. "
                "Requires optional Drift SDK dependencies."
            ),
            parameters=[
                ToolParameter(
                    name="sub_account_id",
                    type="number",
                    description="Drift subaccount index. Defaults to 0.",
                    required=False,
                )
            ],
            function=drift_get_open_orders,
        )
    )
    tool_registry.register(
        ToolDefinition(
            name="drift_get_order_history",
            description=(
                "Classification: private account history read-only Drift tool. "
                "Get recent Drift order history for the authenticated wallet and one subaccount by scanning recent user-account transactions "
                "and parsing OrderRecord events. Requires optional Drift SDK dependencies and a working Solana RPC."
            ),
            parameters=[
                ToolParameter(
                    name="sub_account_id",
                    type="number",
                    description="Drift subaccount index. Defaults to 0.",
                    required=False,
                ),
                ToolParameter(
                    name="limit",
                    type="number",
                    description="Maximum number of history records to return. Defaults to 20.",
                    required=False,
                ),
                ToolParameter(
                    name="offset",
                    type="number",
                    description="Optional offset inside the matched history records.",
                    required=False,
                ),
            ],
            function=drift_get_order_history,
        )
    )
    tool_registry.register(
        ToolDefinition(
            name="drift_get_fill_history",
            description=(
                "Classification: private account history read-only Drift tool. "
                "Get recent Drift fill history for the authenticated wallet and one subaccount by scanning recent user-account transactions "
                "and parsing OrderActionRecord fill events. Requires optional Drift SDK dependencies and a working Solana RPC."
            ),
            parameters=[
                ToolParameter(
                    name="sub_account_id",
                    type="number",
                    description="Drift subaccount index. Defaults to 0.",
                    required=False,
                ),
                ToolParameter(
                    name="limit",
                    type="number",
                    description="Maximum number of history records to return. Defaults to 20.",
                    required=False,
                ),
                ToolParameter(
                    name="offset",
                    type="number",
                    description="Optional offset inside the matched history records.",
                    required=False,
                ),
            ],
            function=drift_get_fill_history,
        )
    )
    tool_registry.register(
        ToolDefinition(
            name="drift_get_position_history",
            description=(
                "Classification: private account history read-only Drift tool. "
                "Get recent position-affecting Drift history for the authenticated wallet and one subaccount by scanning recent user-account transactions "
                "and parsing SettlePnlRecord, FundingPaymentRecord, and LiquidationRecord events. Requires optional Drift SDK dependencies and a working Solana RPC."
            ),
            parameters=[
                ToolParameter(
                    name="sub_account_id",
                    type="number",
                    description="Drift subaccount index. Defaults to 0.",
                    required=False,
                ),
                ToolParameter(
                    name="limit",
                    type="number",
                    description="Maximum number of history records to return. Defaults to 20.",
                    required=False,
                ),
                ToolParameter(
                    name="offset",
                    type="number",
                    description="Optional offset inside the matched history records.",
                    required=False,
                ),
            ],
            function=drift_get_position_history,
        )
    )
    tool_registry.register(
        ToolDefinition(
            name="drift_get_positions",
            description=(
                "Classification: private read-only Drift account tool. "
                "Get current positions for the authenticated wallet and one Drift subaccount. "
                "Requires optional Drift SDK dependencies."
            ),
            parameters=[
                ToolParameter(
                    name="sub_account_id",
                    type="number",
                    description="Drift subaccount index. Defaults to 0.",
                    required=False,
                )
            ],
            function=drift_get_positions,
        )
    )
    tool_registry.register(
        ToolDefinition(
            name="drift_get_open_positions",
            description=(
                "Classification: private read-only Drift account tool. "
                "Get open perp positions for the authenticated wallet and one Drift subaccount. "
                "Requires optional Drift SDK dependencies."
            ),
            parameters=[
                ToolParameter(
                    name="sub_account_id",
                    type="number",
                    description="Drift subaccount index. Defaults to 0.",
                    required=False,
                )
            ],
            function=drift_get_open_positions,
        )
    )


__all__ = [
    "drift_get_account_context",
    "drift_get_account_snapshot",
    "drift_get_balances",
    "drift_get_collateral",
    "drift_get_open_orders",
    "drift_get_order_history",
    "drift_get_fill_history",
    "drift_get_position_history",
    "drift_get_positions",
    "drift_get_open_positions",
    "register_drift_readonly_tools",
]
