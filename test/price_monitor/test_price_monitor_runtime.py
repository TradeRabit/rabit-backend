from types import SimpleNamespace

import pytest

from agents.tools.market import price_monitor_tools
from ws.price.monitor import PriceAlert, PriceMonitor


@pytest.mark.asyncio
async def test_add_price_alert_returns_default_prompt_templates(monkeypatch):
    monitor = PriceMonitor()
    monitor.price_cache["BTC"] = {"price": 94500.0, "timestamp": "now"}

    monkeypatch.setattr(price_monitor_tools, "get_price_monitor", lambda: monitor)
    monkeypatch.setattr(price_monitor_tools, "get_current_scope_id", lambda: "scope-1")
    monkeypatch.setattr(price_monitor_tools, "get_current_user_id", lambda: "wallet:user-1")
    monkeypatch.setattr(
        price_monitor_tools,
        "get_monitoring_cost_service",
        lambda: SimpleNamespace(get_scope_summary=lambda **kwargs: {"scope_id": "scope-1", "total_cost_usd": 0.001}),
    )

    result = await price_monitor_tools.add_price_alert(
        symbol="BTC",
        validation_price=95000,
        invalidation_price=90000,
        direction="LONG",
        exchange="drift",
        trade_label="Trade A",
        trade_id="trade_a",
        setup_id="setup_a",
    )

    assert result["success"] is True
    assert result["scope_id"] == "scope-1"
    assert result["user_id"] == "wallet:user-1"
    assert result["trade_label"] == "Trade A"
    assert result["trade_id"] == "trade_a"
    assert result["setup_id"] == "setup_a"
    assert result["default_prompts"]["validation"] == "Trade A hit validation price at $95,000.00 on DRIFT for BTC."
    assert result["default_prompts"]["invalidation"] == "Trade A hit invalidation price at $90,000.00 on DRIFT for BTC."


@pytest.mark.asyncio
async def test_price_monitor_broadcasts_structured_trigger_event():
    class DummyMonitoringCosts:
        def record_alert_started(self, **kwargs):
            return None

        def record_alert_triggered(self, **kwargs):
            return None

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr("ws.price.monitor.get_monitoring_cost_service", lambda: DummyMonitoringCosts())

    market_handler = SimpleNamespace(get_price=lambda symbol: SimpleNamespace(price=95050.0))
    monitor = PriceMonitor(poll_interval=1, market_handler=market_handler)
    monitor.add_alert(
        symbol="BTC",
        validation_price=95000,
        invalidation_price=90000,
        direction="LONG",
        exchange="drift",
        trade_label="Trade A",
        trade_id="trade_a",
    )
    queue = monitor.subscribe()

    alerts = list(monitor.alerts.values())
    trigger_type = alerts[0].check_price(95050.0)

    assert trigger_type == "VALIDATION"

    await monitor._broadcast_alerts(alerts)
    event = await queue.get()

    assert event["type"] == "price_alert_triggered"
    assert event["count"] == 1
    alert = event["alerts"][0]
    assert alert["trade_label"] == "Trade A"
    assert alert["trade_id"] == "trade_a"
    assert alert["trigger_type"] == "VALIDATION"
    assert alert["trigger_price"] == 95050.0
    assert alert["default_prompt"] == "Trade A hit validation price at $95,050.00 on DRIFT for BTC."
    monkeypatch.undo()


@pytest.mark.asyncio
async def test_price_monitor_callback_receives_default_prompt_event():
    class DummyMonitoringCosts:
        def record_alert_started(self, **kwargs):
            return None

        def record_alert_triggered(self, **kwargs):
            return None

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr("ws.price.monitor.get_monitoring_cost_service", lambda: DummyMonitoringCosts())

    received = []

    async def capture(event):
        received.append(event)

    market_handler = SimpleNamespace(get_price=lambda symbol: SimpleNamespace(price=2990.0))
    monitor = PriceMonitor(poll_interval=1, market_handler=market_handler, alert_callback=capture)
    monitor.add_alert(
        symbol="ETH",
        validation_price=3000,
        invalidation_price=3200,
        direction="SHORT",
        exchange="backpack",
        setup_id="eth_short_setup",
    )

    alert = list(monitor.alerts.values())[0]
    assert alert.check_price(2990.0) == "VALIDATION"

    await monitor._notify_agent([alert])

    assert len(received) == 1
    payload = received[0]
    assert payload["type"] == "price_alert_triggered"
    assert payload["setup_id"] == "eth_short_setup"
    assert payload["default_prompt"] == "eth_short_setup hit validation price at $2,990.00 on BACKPACK for ETH."
    assert payload["message"] == payload["default_prompt"]
    monkeypatch.undo()


def test_price_alert_to_dict_includes_trigger_prompt():
    alert = PriceAlert(
        alert_id="btc_alert",
        symbol="BTC",
        validation_price=95000,
        invalidation_price=90000,
        direction="LONG",
        exchange="binance",
        trade_label="BTC breakout",
    )

    assert alert.check_price(95123.45) == "VALIDATION"

    data = alert.to_dict()
    assert data["trade_label"] == "BTC breakout"
    assert data["default_prompt"] == "BTC breakout hit validation price at $95,123.45 on BINANCE for BTC."


def test_price_monitor_filters_alerts_by_scope_and_user(monkeypatch):
    class DummyMonitoringCosts:
        def record_alert_started(self, **kwargs):
            return None

    monkeypatch.setattr("ws.price.monitor.get_monitoring_cost_service", lambda: DummyMonitoringCosts())

    monitor = PriceMonitor()
    monitor.add_alert(
        symbol="BTC",
        validation_price=95000,
        invalidation_price=90000,
        direction="LONG",
        exchange="drift",
        scope_id="scope-a",
        user_id="wallet:user-a",
    )
    monitor.add_alert(
        symbol="ETH",
        validation_price=3000,
        invalidation_price=3200,
        direction="SHORT",
        exchange="backpack",
        scope_id="scope-b",
        user_id="wallet:user-b",
    )

    scoped_alerts = monitor.list_alerts(scope_id="scope-a")
    user_alerts = monitor.list_alerts(user_id="wallet:user-b")

    assert len(scoped_alerts) == 1
    assert scoped_alerts[0]["symbol"] == "BTC"
    assert len(user_alerts) == 1
    assert user_alerts[0]["symbol"] == "ETH"
