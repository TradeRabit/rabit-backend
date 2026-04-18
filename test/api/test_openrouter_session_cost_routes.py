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
            "phases": [
                {
                    "phase": "intent_router",
                    "calls": 1,
                    "input_tokens": 300,
                    "output_tokens": 50,
                    "total_tokens": 350,
                    "estimated_cost_usd": 0.00165,
                },
                {
                    "phase": "response",
                    "calls": 2,
                    "input_tokens": 2700,
                    "output_tokens": 850,
                    "total_tokens": 3550,
                    "estimated_cost_usd": 0.01065,
                },
            ],
            "created_at": "2026-04-18T00:00:00+00:00",
            "updated_at": "2026-04-18T00:05:00+00:00",
        }


def create_test_client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_get_openrouter_session_cost_returns_summary(monkeypatch):
    monkeypatch.setattr(
        "api.routes.get_openrouter_session_cost_service",
        lambda: DummySessionCostService(),
    )

    client = create_test_client()
    response = client.get("/api/openrouter/session-costs/chat-123?user_id=wallet:user-1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["scope_id"] == "chat-123"
    assert payload["user_id"] == "wallet:user-1"
    assert payload["total_calls"] == 3
    assert payload["estimated_cost_usd"] == 0.0123
    assert payload["phases"][0]["phase"] == "intent_router"


def test_get_openrouter_session_cost_rejects_wrong_owner(monkeypatch):
    monkeypatch.setattr(
        "api.routes.get_openrouter_session_cost_service",
        lambda: DummySessionCostService(),
    )

    client = create_test_client()
    response = client.get("/api/openrouter/session-costs/chat-123?user_id=wallet:someone-else")

    assert response.status_code == 403
