from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import router


class DummySessionCostService:
    def get_scope_summary(self, *, scope_id):
        if scope_id != "chat-123":
            return None
        return {
            "scope_id": "chat-123",
            "user_id": "wallet:user-1",
            "currency": "USD",
            "total_calls": 3,
            "total_input_tokens": 3000,
            "total_output_tokens": 900,
            "total_tokens": 3900,
            "estimated_cost_usd": 0.0123,
            "model_ids": ["anthropic/claude-3.5-sonnet"],
            "phases": [],
            "created_at": "2026-04-18T00:00:00+00:00",
            "updated_at": "2026-04-18T00:05:00+00:00",
        }


class DummyMonitoringCostService:
    def get_scope_summary(self, *, scope_id):
        if scope_id != "chat-123":
            return None
        return {
            "scope_id": "chat-123",
            "user_id": "wallet:user-1",
            "currency": "USD",
            "alert_setup_cost_usd": 0.001,
            "trigger_cost_usd": 0.0005,
            "monitoring_cost_usd": 0.01,
            "total_cost_usd": 0.0115,
            "alert_setup_count": 1,
            "trigger_count": 1,
            "active_alert_count": 0,
            "active_symbol_count": 0,
            "active_symbols": [],
            "total_symbol_hours": 5.0,
            "created_at": "2026-04-18T00:01:00+00:00",
            "updated_at": "2026-04-18T00:06:00+00:00",
        }


def create_test_client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_get_service_cost_returns_combined_summary(monkeypatch):
    monkeypatch.setattr(
        "api.routes.get_openrouter_session_cost_service",
        lambda: DummySessionCostService(),
    )
    monkeypatch.setattr(
        "api.routes.get_monitoring_cost_service",
        lambda: DummyMonitoringCostService(),
    )

    client = create_test_client()
    response = client.get("/api/service-costs/chat-123?user_id=wallet:user-1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["scope_id"] == "chat-123"
    assert payload["model_cost_usd"] == 0.0123
    assert payload["monitor_cost_usd"] == 0.0115
    assert payload["total_cost_usd"] == 0.0238
    assert payload["monitoring_cost"]["trigger_count"] == 1
    assert payload["onchain_ai_usage"]["model_cost_usd"] == 0.0123
    assert payload["onchain_ai_usage"]["service_cost_usd"] == 0.0115
    assert payload["onchain_ai_usage"]["base_cost_units"] == 12300
    assert payload["onchain_ai_usage"]["service_cost_units"] == 11500
    assert payload["onchain_ai_usage"]["total_charged_units"] == 26239
    assert payload["onchain_ai_usage"]["instruction_buildable"] is False
    assert payload["onchain_ai_usage"]["model_id"] == "anthropic/claude-3.5-sonnet"


def test_get_service_cost_rejects_wrong_owner(monkeypatch):
    monkeypatch.setattr(
        "api.routes.get_openrouter_session_cost_service",
        lambda: DummySessionCostService(),
    )
    monkeypatch.setattr(
        "api.routes.get_monitoring_cost_service",
        lambda: DummyMonitoringCostService(),
    )

    client = create_test_client()
    response = client.get("/api/service-costs/chat-123?user_id=wallet:someone-else")

    assert response.status_code == 403
