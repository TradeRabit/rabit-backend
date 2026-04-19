from agents.service_costs.monitoring import MonitoringCostDatabase, MonitoringCostService


def test_monitoring_cost_service_tracks_alert_lifecycle(tmp_path):
    db = MonitoringCostDatabase(str(tmp_path / "monitoring_costs.json"))
    service = MonitoringCostService(db)

    service.record_alert_started(
        scope_id="scope-1",
        user_id="wallet:user-1",
        alert_id="btc-alert",
        symbol="BTC",
        exchange="drift",
        direction="LONG",
        started_at="2026-04-19T00:00:00+00:00",
    )
    service.record_alert_triggered(
        scope_id="scope-1",
        alert_id="btc-alert",
        triggered_at="2026-04-19T01:00:00+00:00",
        trigger_type="VALIDATION",
        trigger_price=95000.0,
    )

    summary = service.get_scope_summary(scope_id="scope-1")

    assert summary["scope_id"] == "scope-1"
    assert summary["user_id"] == "wallet:user-1"
    assert summary["alert_setup_count"] == 1
    assert summary["trigger_count"] == 1
    assert summary["active_alert_count"] == 0
    assert summary["active_symbol_count"] == 0
    assert summary["total_symbol_hours"] == 1.0
    assert summary["alert_setup_cost_usd"] == 0.001
    assert summary["monitoring_cost_usd"] == 0.002
    assert summary["trigger_cost_usd"] == 0.0005
    assert summary["total_cost_usd"] == 0.0035


def test_monitoring_cost_service_deduplicates_same_symbol_windows(tmp_path):
    db = MonitoringCostDatabase(str(tmp_path / "monitoring_costs.json"))
    service = MonitoringCostService(db)

    service.record_alert_started(
        scope_id="scope-2",
        user_id="wallet:user-2",
        alert_id="btc-1",
        symbol="BTC",
        exchange="drift",
        direction="LONG",
        started_at="2026-04-19T00:00:00+00:00",
    )
    service.record_alert_started(
        scope_id="scope-2",
        user_id="wallet:user-2",
        alert_id="btc-2",
        symbol="BTC",
        exchange="drift",
        direction="LONG",
        started_at="2026-04-19T00:30:00+00:00",
    )
    service.record_alert_removed(
        scope_id="scope-2",
        alert_id="btc-1",
        removed_at="2026-04-19T00:45:00+00:00",
    )
    service.record_alert_triggered(
        scope_id="scope-2",
        alert_id="btc-2",
        triggered_at="2026-04-19T01:30:00+00:00",
        trigger_type="VALIDATION",
        trigger_price=95100.0,
    )

    summary = service.get_scope_summary(scope_id="scope-2")

    assert summary["alert_setup_count"] == 2
    assert summary["trigger_count"] == 1
    assert summary["total_symbol_hours"] == 1.5
    assert summary["monitoring_cost_usd"] == 0.003
    assert summary["total_cost_usd"] == 0.0055
