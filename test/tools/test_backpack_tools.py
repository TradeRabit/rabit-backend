import asyncio

from agents.tools import tool_registry
from agents.tools.backpack_execution.backpack_tools import (
    backpack_get_collateral,
    backpack_place_order,
)
from agents.tools.core.runtime_context import (
    reset_current_backpack_execution,
    reset_current_user_id,
    set_current_backpack_execution,
    set_current_user_id,
)
from agents.tools_registry.register_tools import register_trading_tools


class DummyBackpackClient:
    def ensure_credentials(self):
        return None

    async def get_collateral(self, subaccount_id=None):
        return {"collateral": 123.45, "subaccount_id": subaccount_id}

    async def place_order(self, **kwargs):
        return {"status": "accepted", "order": kwargs}


class DummyConnectionService:
    def __init__(self, credentials):
        self.credentials = credentials
        self.calls = []

    def get_active_credentials(self, **kwargs):
        self.calls.append(kwargs)
        return dict(self.credentials)


def test_register_trading_tools_includes_backpack_tools(monkeypatch):
    monkeypatch.setattr("agents.tools_registry.register_tools.register_tradingview_tools", lambda: None)
    monkeypatch.setattr("agents.tools_registry.register_tools.settings.WEB_SEARCH_ENABLED", False)
    monkeypatch.setattr("agents.tools_registry.register_tools.settings.MEMORY_TOOLS_ENABLED", False)

    register_trading_tools()
    registered = {tool.name for tool in tool_registry.list_tools()}

    assert "backpack_get_balances" in registered
    assert "backpack_get_collateral" in registered
    assert "backpack_get_open_orders" in registered
    assert "backpack_place_order" in registered
    assert "backpack_cancel_order" in registered


def test_backpack_read_tool_works_without_execution_gate(monkeypatch):
    monkeypatch.setattr(
        "agents.tools.backpack_execution.backpack_tools.get_backpack_client",
        lambda: DummyBackpackClient(),
    )
    token = set_current_backpack_execution({"enabled": False, "exchange": "backpack"})
    try:
        result = asyncio.run(backpack_get_collateral(subaccount_id=7))
    finally:
        reset_current_backpack_execution(token)

    assert result["exchange"] == "backpack"
    assert result["data"]["collateral"] == 123.45
    assert result["data"]["subaccount_id"] == 7


def test_backpack_execution_tool_respects_gate(monkeypatch):
    monkeypatch.setattr(
        "agents.tools.backpack_execution.backpack_tools.get_backpack_client",
        lambda: DummyBackpackClient(),
    )
    monkeypatch.setattr(
        "agents.tools.backpack_execution.backpack_tools.is_backpack_execution_allowed",
        lambda config: False,
    )

    token = set_current_backpack_execution({"enabled": False, "exchange": "backpack"})
    try:
        try:
            asyncio.run(
                backpack_place_order(
                    symbol="BTC_USDC",
                    side="Bid",
                    order_type="Limit",
                    quantity="0.01",
                    price="100000",
                )
            )
        except ValueError as exc:
            assert "disabled" in str(exc)
        else:
            raise AssertionError("Expected backpack_place_order to be blocked by the execution gate")
    finally:
        reset_current_backpack_execution(token)


def test_backpack_execution_tool_runs_when_gate_is_open(monkeypatch):
    monkeypatch.setattr(
        "agents.tools.backpack_execution.backpack_tools.get_backpack_client",
        lambda: DummyBackpackClient(),
    )
    monkeypatch.setattr(
        "agents.tools.backpack_execution.backpack_tools.is_backpack_execution_allowed",
        lambda config: True,
    )

    token = set_current_backpack_execution({"enabled": True, "exchange": "backpack"})
    try:
        result = asyncio.run(
            backpack_place_order(
                symbol="BTC_USDC",
                side="Bid",
                order_type="Limit",
                quantity="0.01",
                price="100000",
                time_in_force="GTC",
                post_only=True,
            )
        )
    finally:
        reset_current_backpack_execution(token)

    assert result["exchange"] == "backpack"
    assert result["execution_enabled"] is True
    assert result["data"]["status"] == "accepted"
    assert result["data"]["order"]["symbol"] == "BTC_USDC"


def test_backpack_tools_prefer_active_user_connection(monkeypatch):
    service = DummyConnectionService(
        {
            "connection_id": "conn-1",
            "exchange": "backpack",
            "label": "Primary",
            "api_key": "user-api-key",
            "api_secret": "user-api-secret",
            "trading_enabled": True,
            "read_only": False,
        }
    )
    captured = {}

    class CaptureClient:
        def __init__(self, api_key=None, api_secret=None, **kwargs):
            captured["api_key"] = api_key
            captured["api_secret"] = api_secret

        async def get_collateral(self, subaccount_id=None):
            return {"subaccount_id": subaccount_id, "ok": True}

    monkeypatch.setattr(
        "agents.tools.backpack_execution.backpack_tools.get_exchange_connection_service",
        lambda: service,
    )
    monkeypatch.setattr(
        "agents.tools.backpack_execution.backpack_tools.BackpackClient",
        CaptureClient,
    )

    user_token = set_current_user_id("user-42")
    execution_token = set_current_backpack_execution({"enabled": False, "exchange": "backpack"})
    try:
        result = asyncio.run(backpack_get_collateral(subaccount_id=3))
    finally:
        reset_current_backpack_execution(execution_token)
        reset_current_user_id(user_token)

    assert captured["api_key"] == "user-api-key"
    assert captured["api_secret"] == "user-api-secret"
    assert service.calls[0]["user_id"] == "user-42"
    assert service.calls[0]["exchange"] == "backpack"
    assert service.calls[0]["require_trading_enabled"] is False
    assert result["data"]["ok"] is True
