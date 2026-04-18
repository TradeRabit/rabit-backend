import asyncio

from agents.tools import tool_registry
from agents.tools.core.runtime_context import (
    reset_current_drift_execution,
    reset_current_user_id,
    set_current_drift_execution,
    set_current_user_id,
)
from agents.tools.drift_execution.drift_execution_tools import (
    drift_cancel_order,
    drift_place_order,
)
from agents.tools_registry.register_tools import register_trading_tools


class DummyDriftExecutionRequestService:
    def __init__(self):
        self.created = []

    def create_prepared_request(self, **kwargs):
        self.created.append(kwargs)
        return {
            "execution_id": "exec-tool-1",
            "status": "prepared",
            "mode": "client_wallet_signing",
            "user_id": kwargs["user_id"],
            "auth_wallet_address": kwargs["auth_wallet_address"],
            "execution_wallet_address": kwargs["execution_wallet_status"]["execution_wallet_address"],
            "same_wallet_required": True,
            "sub_account_id": kwargs["sub_account_id"],
            "order_intent": kwargs["order_intent"],
            "requires_client_signature": True,
            "prepared_transaction": kwargs["prepared_transaction"],
            "prepared_at": "2026-04-18T00:00:00+00:00",
            "expires_at": "2026-04-18T00:15:00+00:00",
            "submitted_at": None,
            "transaction_signature": None,
            "last_error": None,
        }


class DummyDriftExecutionTxBuilder:
    def __init__(self):
        self.place_calls = []
        self.cancel_calls = []

    async def build_place_perp_order_payload(self, **kwargs):
        self.place_calls.append(kwargs)
        return {
            "classification": "same_wallet_mobile_signing_payload",
            "action": "place_perp_order",
            "unsigned_transaction": "unsigned-place",
        }

    async def build_cancel_order_payload(self, **kwargs):
        self.cancel_calls.append(kwargs)
        return {
            "classification": "same_wallet_mobile_signing_payload",
            "action": "cancel_order",
            "unsigned_transaction": "unsigned-cancel",
        }


def test_register_trading_tools_includes_drift_execution_tools(monkeypatch):
    monkeypatch.setattr("agents.tools_registry.register_tools.register_tradingview_tools", lambda: None)
    monkeypatch.setattr("agents.tools_registry.register_tools.settings.WEB_SEARCH_ENABLED", False)
    monkeypatch.setattr("agents.tools_registry.register_tools.settings.MEMORY_TOOLS_ENABLED", False)

    register_trading_tools()
    registered = {tool.name for tool in tool_registry.list_tools()}

    assert "drift_place_order" in registered
    assert "drift_cancel_order" in registered


def test_drift_place_order_respects_execution_gate(monkeypatch):
    monkeypatch.setattr(
        "agents.tools.drift_execution.drift_execution_tools.is_drift_execution_allowed",
        lambda config: False,
    )

    user_token = set_current_user_id("wallet:So11111111111111111111111111111111111111112")
    execution_token = set_current_drift_execution({"enabled": False, "exchange": "drift"})
    try:
        try:
            asyncio.run(
                drift_place_order(
                    side="long",
                    order_type="limit",
                    base_asset_amount="1000",
                    market_index=5,
                    price="100",
                )
            )
        except ValueError as exc:
            assert "disabled" in str(exc)
        else:
            raise AssertionError("Expected drift_place_order to be blocked by execution gate")
    finally:
        reset_current_drift_execution(execution_token)
        reset_current_user_id(user_token)


def test_drift_place_order_builds_prepared_request(monkeypatch):
    builder = DummyDriftExecutionTxBuilder()
    service = DummyDriftExecutionRequestService()
    monkeypatch.setattr(
        "agents.tools.drift_execution.drift_execution_tools.is_drift_execution_allowed",
        lambda config: True,
    )
    monkeypatch.setattr(
        "agents.tools.drift_execution.drift_execution_tools.get_drift_execution_tx_builder",
        lambda: builder,
    )
    monkeypatch.setattr(
        "agents.tools.drift_execution.drift_execution_tools.get_drift_execution_request_service",
        lambda: service,
    )

    user_token = set_current_user_id("wallet:So11111111111111111111111111111111111111112")
    execution_token = set_current_drift_execution({"enabled": True, "exchange": "drift"})
    try:
        result = asyncio.run(
            drift_place_order(
                side="long",
                order_type="limit",
                base_asset_amount="1000",
                market_index=5,
                symbol="SOL-PERP",
                price="100",
            )
        )
    finally:
        reset_current_drift_execution(execution_token)
        reset_current_user_id(user_token)

    assert result["exchange"] == "drift"
    assert result["execution_enabled"] is True
    assert result["execution_id"] == "exec-tool-1"
    assert result["data"]["prepared_transaction"]["unsigned_transaction"] == "unsigned-place"
    assert builder.place_calls[0]["order_intent"]["market_index"] == 5
    assert service.created[0]["execution_wallet_status"]["mode"] == "same_wallet"


def test_drift_cancel_order_builds_prepared_request(monkeypatch):
    builder = DummyDriftExecutionTxBuilder()
    service = DummyDriftExecutionRequestService()
    monkeypatch.setattr(
        "agents.tools.drift_execution.drift_execution_tools.is_drift_execution_allowed",
        lambda config: True,
    )
    monkeypatch.setattr(
        "agents.tools.drift_execution.drift_execution_tools.get_drift_execution_tx_builder",
        lambda: builder,
    )
    monkeypatch.setattr(
        "agents.tools.drift_execution.drift_execution_tools.get_drift_execution_request_service",
        lambda: service,
    )

    user_token = set_current_user_id("wallet:So11111111111111111111111111111111111111112")
    execution_token = set_current_drift_execution({"enabled": True, "exchange": "drift"})
    try:
        result = asyncio.run(drift_cancel_order(order_id="77"))
    finally:
        reset_current_drift_execution(execution_token)
        reset_current_user_id(user_token)

    assert result["exchange"] == "drift"
    assert result["execution_id"] == "exec-tool-1"
    assert result["data"]["prepared_transaction"]["action"] == "cancel_order"
    assert builder.cancel_calls[0]["order_id"] == "77"
