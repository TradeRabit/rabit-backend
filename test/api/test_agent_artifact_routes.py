from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import router


class DummyArtifactService:
    def list_scope_artifacts(self, *, scope_id):
        if scope_id != "scope-1":
            return None
        return {
            "scope_id": "scope-1",
            "user_id": "wallet:user-1",
            "created_at": "2026-04-19T00:00:00+00:00",
            "updated_at": "2026-04-19T00:05:00+00:00",
            "artifacts": [
                {
                    "artifact_id": "artifact-1",
                    "scope_id": "scope-1",
                    "user_id": "wallet:user-1",
                    "node_name": "chart_analysis",
                    "kind": "chart_write_screenshot",
                    "payload": {
                        "effective_symbol": "BTC",
                        "screenshot_url": "http://localhost/chart.png",
                    },
                    "metadata": {"symbol_change_blocked": False},
                    "created_at": "2026-04-19T00:00:00+00:00",
                    "expires_at": "2026-04-26T00:00:00+00:00",
                }
            ],
        }


def create_test_client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_get_agent_pipeline_artifacts_returns_scope_summary(monkeypatch):
    monkeypatch.setattr(
        "api.routes.get_pipeline_artifact_service",
        lambda: DummyArtifactService(),
    )

    client = create_test_client()
    response = client.get("/api/agent/artifacts/scope-1?user_id=wallet:user-1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["scope_id"] == "scope-1"
    assert payload["user_id"] == "wallet:user-1"
    assert payload["total"] == 1
    assert payload["artifacts"][0]["artifact_id"] == "artifact-1"
    assert payload["artifacts"][0]["kind"] == "chart_write_screenshot"


def test_get_agent_pipeline_artifacts_rejects_wrong_owner(monkeypatch):
    monkeypatch.setattr(
        "api.routes.get_pipeline_artifact_service",
        lambda: DummyArtifactService(),
    )

    client = create_test_client()
    response = client.get("/api/agent/artifacts/scope-1?user_id=wallet:someone-else")

    assert response.status_code == 403
