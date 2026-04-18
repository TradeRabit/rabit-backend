from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
import jwt

from agents.uploads import TemporaryUploadManager
from api.routes import router


class DummyAgent:
    def __init__(self):
        self.calls = []
        self.last_conversation_style = "normal"
        self.last_trading_style = "balanced"
        self.last_market_context = {"scope_mode": "global", "market_state": {}}
        self.last_backpack_execution = {"enabled": False, "exchange": "backpack"}
        self.last_drift_execution = {"enabled": False, "exchange": "drift"}
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
        market_context=None,
        backpack_execution=None,
        drift_execution=None,
    ):
        self.last_conversation_style = conversation_style
        self.last_trading_style = trading_style
        self.last_market_context = market_context or {"scope_mode": "global", "market_state": {}}
        self.last_backpack_execution = backpack_execution or {"enabled": False, "exchange": "backpack"}
        self.last_drift_execution = drift_execution or {"enabled": False, "exchange": "drift"}
        self.calls.append({
            "message": message,
            "attachments": attachments or [],
            "conversation_style": conversation_style,
            "trading_style": trading_style,
            "market_context": market_context,
            "backpack_execution": backpack_execution,
            "drift_execution": drift_execution,
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
            "market_context": {
                "scope_mode": "locked_asset",
                "asset_id": "bitcoin",
                "symbol": "BTC",
                "timeframe": "4H",
                "market_state": {
                    "trend_bias": "bullish",
                    "structure_position": "near_resistance",
                },
            },
            "backpack_execution": {
                "enabled": True,
                "exchange": "backpack",
            },
            "drift_execution": {
                "enabled": False,
                "exchange": "drift",
            },
            "attachment_ids": [payload["file_id"]],
        },
    )
    assert chat_response.status_code == 200
    assert chat_response.json()["response"] == "Agent replied"
    assert chat_response.json()["user_id"] == "user-123"
    assert chat_response.json()["conversation_style"] == "formal"
    assert chat_response.json()["trading_style"] == "smart_money"
    assert chat_response.json()["market_context"]["scope_mode"] == "locked_asset"
    assert chat_response.json()["market_context"]["symbol"] == "BTC"
    assert chat_response.json()["backpack_execution"]["enabled"] is True
    assert chat_response.json()["backpack_execution"]["exchange"] == "backpack"
    assert chat_response.json()["drift_execution"]["enabled"] is False
    assert chat_response.json()["drift_execution"]["exchange"] == "drift"
    assert chat_response.json()["intent"]["intent"] == "market_analysis"
    assert agent.calls[0]["message"] == "Review this chart"
    assert agent.calls[0]["conversation_style"] == "formal"
    assert agent.calls[0]["trading_style"] == "smart_money"
    assert agent.calls[0]["market_context"]["scope_mode"] == "locked_asset"
    assert agent.calls[0]["backpack_execution"]["enabled"] is True
    assert agent.calls[0]["drift_execution"]["enabled"] is False
    assert len(agent.calls[0]["attachments"]) == 1
    assert agent.calls[0]["attachments"][0].filename == "chart.png"
    assert captured["scope_id"] == "user:test"
    assert captured["user_id"] == "user-123"

    delete_response = client.delete(f"/api/agent/uploads/{payload['file_id']}")
    assert delete_response.status_code == 200
    assert delete_response.json()["success"] is True


def test_agent_chat_prefers_authenticated_user_id(monkeypatch, tmp_path: Path):
    manager = TemporaryUploadManager(storage_dir=tmp_path, ttl_seconds=3600, max_size_mb=1)
    agent = DummyAgent()

    monkeypatch.setattr("api.routes.get_upload_manager", lambda: manager)
    monkeypatch.setattr("api.routes.get_agent", lambda scope_id=None, user_id=None: agent)
    monkeypatch.setattr("api.routes.settings.AUTH_JWT_SECRET", "test-jwt-secret")

    token = jwt.encode(
        {
            "sub": "WalletAddress",
            "user_id": "wallet:WalletAddress",
            "wallet_address": "WalletAddress",
            "iss": "rabit-backend",
            "aud": "rabit-mobile",
            "iat": 1,
            "exp": 4102444800,
        },
        "test-jwt-secret",
        algorithm="HS256",
    )

    client = create_test_client()
    response = client.post(
        "/api/agent/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "message": "Review this chart",
            "user_id": "wallet:WalletAddress",
            "attachment_ids": [],
        },
    )

    assert response.status_code == 200
    assert response.json()["user_id"] == "wallet:WalletAddress"
