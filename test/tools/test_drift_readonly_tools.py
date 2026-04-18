import asyncio

from agents.tools import tool_registry
from agents.tools.drift_execution.drift_readonly_tools import (
    drift_get_account_context,
    drift_get_account_snapshot,
    drift_get_balances,
    drift_get_collateral,
    drift_get_fill_history,
    drift_get_open_orders,
    drift_get_order_history,
    drift_get_position_history,
    drift_get_positions,
    drift_get_open_positions,
)
from agents.tools.core.runtime_context import (
    reset_current_drift_execution,
    reset_current_market_context,
    reset_current_user_id,
    set_current_drift_execution,
    set_current_market_context,
    set_current_user_id,
)
from agents.tools_registry.register_tools import register_trading_tools


def test_register_trading_tools_includes_drift_readonly_tools(monkeypatch):
    monkeypatch.setattr("agents.tools_registry.register_tools.register_tradingview_tools", lambda: None)
    monkeypatch.setattr("agents.tools_registry.register_tools.settings.WEB_SEARCH_ENABLED", False)
    monkeypatch.setattr("agents.tools_registry.register_tools.settings.MEMORY_TOOLS_ENABLED", False)

    register_trading_tools()
    registered = {tool.name for tool in tool_registry.list_tools()}

    assert "drift_get_account_context" in registered
    assert "drift_get_account_snapshot" in registered
    assert "drift_get_balances" in registered
    assert "drift_get_collateral" in registered
    assert "drift_get_open_orders" in registered
    assert "drift_get_order_history" in registered
    assert "drift_get_fill_history" in registered
    assert "drift_get_positions" in registered
    assert "drift_get_open_positions" in registered
    assert "drift_get_position_history" in registered


def test_drift_get_account_context_returns_wallet_and_market_context():
    user_token = set_current_user_id("wallet:So11111111111111111111111111111111111111112")
    market_token = set_current_market_context(
        {
            "scope_mode": "locked_asset",
            "symbol": "SOL",
            "exchange": "drift",
            "timeframe": "1h",
        }
    )
    execution_token = set_current_drift_execution({"enabled": False, "exchange": "drift"})
    try:
        result = asyncio.run(drift_get_account_context())
    finally:
        reset_current_drift_execution(execution_token)
        reset_current_market_context(market_token)
        reset_current_user_id(user_token)

    assert result["exchange"] == "drift"
    assert result["classification"] == "account_linked_read_only_context"
    assert result["wallet_address"] == "So11111111111111111111111111111111111111112"
    assert result["authenticated_wallet_linked"] is True
    assert result["execution_wallet"]["mode"] == "same_wallet"
    assert (
        result["execution_wallet"]["execution_wallet_address"]
        == "So11111111111111111111111111111111111111112"
    )
    assert result["execution_wallet"]["verified"] is True
    assert result["market_context"]["symbol"] == "SOL"
    assert result["drift_execution"]["exchange"] == "drift"
    assert result["private_account_reads_available"] is True


class DummyDriftAccountClient:
    async def get_account_snapshot(self, wallet_address, sub_account_id=0):
        return {
            "wallet_address": wallet_address,
            "sub_account_id": sub_account_id,
            "open_orders_count": 2,
            "open_positions_count": 1,
            "spot_balances_count": 1,
            "total_collateral": "1000000",
            "free_collateral": "500000",
            "leverage": "12500",
        }

    async def get_balances(self, wallet_address, sub_account_id=0):
        return {
            "wallet_address": wallet_address,
            "sub_account_id": sub_account_id,
            "count": 1,
            "spot_balances": [{"market_index": 0, "scaled_balance": "1000000"}],
        }

    async def get_collateral(self, wallet_address, sub_account_id=0):
        return {
            "wallet_address": wallet_address,
            "sub_account_id": sub_account_id,
            "total_collateral": "1000000",
            "free_collateral": "500000",
            "leverage": "12500",
        }

    async def get_open_orders(self, wallet_address, sub_account_id=0):
        return {
            "wallet_address": wallet_address,
            "sub_account_id": sub_account_id,
            "count": 2,
            "open_orders": [{"market_index": 0}, {"market_index": 1}],
        }

    async def get_open_positions(self, wallet_address, sub_account_id=0):
        return {
            "wallet_address": wallet_address,
            "sub_account_id": sub_account_id,
            "count": 1,
            "open_positions": [{"market_index": 0, "base_asset_amount": "1000000"}],
        }

    async def get_positions(self, wallet_address, sub_account_id=0):
        return await self.get_open_positions(wallet_address, sub_account_id)

    async def get_order_history(self, wallet_address, sub_account_id=0, limit=20, offset=0):
        return {
            "wallet_address": wallet_address,
            "sub_account_id": sub_account_id,
            "count": 1,
            "limit": limit,
            "offset": offset,
            "order_history": [{"event_type": "OrderRecord", "tx_signature": "sig-1"}],
        }

    async def get_fill_history(self, wallet_address, sub_account_id=0, limit=20, offset=0):
        return {
            "wallet_address": wallet_address,
            "sub_account_id": sub_account_id,
            "count": 1,
            "limit": limit,
            "offset": offset,
            "fill_history": [{"event_type": "OrderActionRecord", "tx_signature": "sig-2"}],
        }

    async def get_position_history(self, wallet_address, sub_account_id=0, limit=20, offset=0):
        return {
            "wallet_address": wallet_address,
            "sub_account_id": sub_account_id,
            "count": 1,
            "limit": limit,
            "offset": offset,
            "position_history": [{"event_type": "SettlePnlRecord", "tx_signature": "sig-3"}],
        }


def test_drift_private_account_tools_require_authenticated_wallet(monkeypatch):
    monkeypatch.setattr(
        "agents.tools.drift_execution.drift_readonly_tools.get_drift_account_client",
        lambda: DummyDriftAccountClient(),
    )

    try:
        asyncio.run(drift_get_account_snapshot())
    except ValueError as exc:
        assert "authenticated wallet user" in str(exc)
    else:
        raise AssertionError("Expected wallet auth requirement for Drift private account tools")


def test_drift_get_account_snapshot_uses_authenticated_wallet(monkeypatch):
    monkeypatch.setattr(
        "agents.tools.drift_execution.drift_readonly_tools.get_drift_account_client",
        lambda: DummyDriftAccountClient(),
    )
    user_token = set_current_user_id("wallet:So11111111111111111111111111111111111111112")
    try:
        result = asyncio.run(drift_get_account_snapshot(sub_account_id=2))
    finally:
        reset_current_user_id(user_token)

    assert result["classification"] == "private_account_read_only"
    assert result["data"]["wallet_address"] == "So11111111111111111111111111111111111111112"
    assert result["data"]["sub_account_id"] == 2
    assert result["data"]["open_orders_count"] == 2


def test_drift_get_open_orders_uses_authenticated_wallet(monkeypatch):
    monkeypatch.setattr(
        "agents.tools.drift_execution.drift_readonly_tools.get_drift_account_client",
        lambda: DummyDriftAccountClient(),
    )
    user_token = set_current_user_id("wallet:So11111111111111111111111111111111111111112")
    try:
        result = asyncio.run(drift_get_open_orders())
    finally:
        reset_current_user_id(user_token)

    assert result["classification"] == "private_account_read_only"
    assert result["data"]["count"] == 2
    assert result["data"]["open_orders"][0]["market_index"] == 0


def test_drift_get_balances_uses_authenticated_wallet(monkeypatch):
    monkeypatch.setattr(
        "agents.tools.drift_execution.drift_readonly_tools.get_drift_account_client",
        lambda: DummyDriftAccountClient(),
    )
    user_token = set_current_user_id("wallet:So11111111111111111111111111111111111111112")
    try:
        result = asyncio.run(drift_get_balances())
    finally:
        reset_current_user_id(user_token)

    assert result["classification"] == "private_account_read_only"
    assert result["data"]["count"] == 1
    assert result["data"]["spot_balances"][0]["market_index"] == 0


def test_drift_get_collateral_uses_authenticated_wallet(monkeypatch):
    monkeypatch.setattr(
        "agents.tools.drift_execution.drift_readonly_tools.get_drift_account_client",
        lambda: DummyDriftAccountClient(),
    )
    user_token = set_current_user_id("wallet:So11111111111111111111111111111111111111112")
    try:
        result = asyncio.run(drift_get_collateral())
    finally:
        reset_current_user_id(user_token)

    assert result["classification"] == "private_account_read_only"
    assert result["data"]["total_collateral"] == "1000000"
    assert result["data"]["free_collateral"] == "500000"
    assert result["data"]["leverage"] == "12500"


def test_drift_get_positions_uses_authenticated_wallet(monkeypatch):
    monkeypatch.setattr(
        "agents.tools.drift_execution.drift_readonly_tools.get_drift_account_client",
        lambda: DummyDriftAccountClient(),
    )
    user_token = set_current_user_id("wallet:So11111111111111111111111111111111111111112")
    try:
        result = asyncio.run(drift_get_positions())
    finally:
        reset_current_user_id(user_token)

    assert result["classification"] == "private_account_read_only"
    assert result["data"]["count"] == 1
    assert result["data"]["open_positions"][0]["market_index"] == 0


def test_drift_get_open_positions_uses_authenticated_wallet(monkeypatch):
    monkeypatch.setattr(
        "agents.tools.drift_execution.drift_readonly_tools.get_drift_account_client",
        lambda: DummyDriftAccountClient(),
    )
    user_token = set_current_user_id("wallet:So11111111111111111111111111111111111111112")
    try:
        result = asyncio.run(drift_get_open_positions())
    finally:
        reset_current_user_id(user_token)

    assert result["classification"] == "private_account_read_only"
    assert result["data"]["count"] == 1
    assert result["data"]["open_positions"][0]["market_index"] == 0


def test_drift_get_order_history_uses_authenticated_wallet(monkeypatch):
    monkeypatch.setattr(
        "agents.tools.drift_execution.drift_readonly_tools.get_drift_account_client",
        lambda: DummyDriftAccountClient(),
    )
    user_token = set_current_user_id("wallet:So11111111111111111111111111111111111111112")
    try:
        result = asyncio.run(drift_get_order_history(limit=5, offset=2))
    finally:
        reset_current_user_id(user_token)

    assert result["classification"] == "private_account_history_read_only"
    assert result["data"]["count"] == 1
    assert result["data"]["limit"] == 5
    assert result["data"]["offset"] == 2
    assert result["data"]["order_history"][0]["event_type"] == "OrderRecord"


def test_drift_get_fill_history_uses_authenticated_wallet(monkeypatch):
    monkeypatch.setattr(
        "agents.tools.drift_execution.drift_readonly_tools.get_drift_account_client",
        lambda: DummyDriftAccountClient(),
    )
    user_token = set_current_user_id("wallet:So11111111111111111111111111111111111111112")
    try:
        result = asyncio.run(drift_get_fill_history(limit=5, offset=1))
    finally:
        reset_current_user_id(user_token)

    assert result["classification"] == "private_account_history_read_only"
    assert result["data"]["count"] == 1
    assert result["data"]["limit"] == 5
    assert result["data"]["offset"] == 1
    assert result["data"]["fill_history"][0]["event_type"] == "OrderActionRecord"


def test_drift_get_position_history_uses_authenticated_wallet(monkeypatch):
    monkeypatch.setattr(
        "agents.tools.drift_execution.drift_readonly_tools.get_drift_account_client",
        lambda: DummyDriftAccountClient(),
    )
    user_token = set_current_user_id("wallet:So11111111111111111111111111111111111111112")
    try:
        result = asyncio.run(drift_get_position_history(limit=3))
    finally:
        reset_current_user_id(user_token)

    assert result["classification"] == "private_account_history_read_only"
    assert result["data"]["count"] == 1
    assert result["data"]["limit"] == 3
    assert result["data"]["position_history"][0]["event_type"] == "SettlePnlRecord"
