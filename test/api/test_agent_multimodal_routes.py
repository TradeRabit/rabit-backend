from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from agents.uploads import TemporaryUploadManager
from api.routes import router


class DummyAgent:
    def __init__(self):
        self.calls = []
        self.last_conversation_style = "normal"
        self.last_trading_style = "balanced"
        self.last_intent = {
            "intent": "market_analysis",
            "goal_summary": "Analyze uploaded chart",
            "confidence": "high",
            "preferred_tool_groups": ["market", "chart", "ui"],
            "routing_reason": "User asks for chart review",
        }

    async def process_trading_query(
        self,
        message,
        attachments=None,
        conversation_style="normal",
        trading_style="balanced",
    ):
        self.last_conversation_style = conversation_style
        self.last_trading_style = trading_style
        self.calls.append({
            "message": message,
            "attachments": attachments or [],
            "conversation_style": conversation_style,
            "trading_style": trading_style,
        })
        return "Agent replied"


def create_test_client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_agent_upload_chat_and_delete(monkeypatch, tmp_path: Path):
    manager = TemporaryUploadManager(storage_dir=tmp_path, ttl_seconds=3600, max_size_mb=1)
    agent = DummyAgent()
    captured = {}

    monkeypatch.setattr("api.routes.get_upload_manager", lambda: manager)

    def fake_get_agent(scope_id=None, user_id=None):
        captured["scope_id"] = scope_id
        captured["user_id"] = user_id
        return agent

    monkeypatch.setattr("api.routes.get_agent", fake_get_agent)

    client = create_test_client()

    upload_response = client.post(
        "/api/agent/uploads",
        files={"file": ("chart.png", b"fake-image", "image/png")},
    )
    assert upload_response.status_code == 200
    payload = upload_response.json()
    assert payload["filename"] == "chart.png"
    assert payload["kind"] == "image"

    chat_response = client.post(
        "/api/agent/chat",
        json={
            "message": "Review this chart",
            "scope_id": "user:test",
            "user_id": "user-123",
            "conversation_style": "formal",
            "trading_style": "smart_money",
            "attachment_ids": [payload["file_id"]],
        },
    )
    assert chat_response.status_code == 200
    assert chat_response.json()["response"] == "Agent replied"
    assert chat_response.json()["user_id"] == "user-123"
    assert chat_response.json()["conversation_style"] == "formal"
    assert chat_response.json()["trading_style"] == "smart_money"
    assert chat_response.json()["intent"]["intent"] == "market_analysis"
    assert agent.calls[0]["message"] == "Review this chart"
    assert agent.calls[0]["conversation_style"] == "formal"
    assert agent.calls[0]["trading_style"] == "smart_money"
    assert len(agent.calls[0]["attachments"]) == 1
    assert agent.calls[0]["attachments"][0].filename == "chart.png"
    assert captured["scope_id"] == "user:test"
    assert captured["user_id"] == "user-123"

    delete_response = client.delete(f"/api/agent/uploads/{payload['file_id']}")
    assert delete_response.status_code == 200
    assert delete_response.json()["success"] is True
