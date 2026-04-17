from fastapi import FastAPI
from fastapi.testclient import TestClient

from agents.uploads import TemporaryUploadManager
from api.routes import router


class DummyStreamingAgent:
    def __init__(self):
        self.calls = []
        self.last_conversation_style = "normal"
        self.last_trading_style = "balanced"
        self.last_intent = {
            "intent": "plan_or_strategy",
            "goal_summary": "Stream a guided plan",
            "confidence": "high",
            "preferred_tool_groups": ["ui", "market"],
            "routing_reason": "User explicitly wants a plan",
        }

    async def process_stream(
        self,
        message,
        event_emitter,
        use_tools=False,
        attachments=None,
        conversation_style="normal",
        trading_style="balanced",
    ):
        self.last_conversation_style = conversation_style
        self.last_trading_style = trading_style
        self.calls.append(
            {
                "message": message,
                "use_tools": use_tools,
                "attachments": attachments or [],
                "conversation_style": conversation_style,
                "trading_style": trading_style,
            }
        )
        await event_emitter(
            "thinking_summary",
            {
                "type": "thinking_summary",
                "summary": "Checking setup before execution",
            },
        )
        await event_emitter(
            "plan",
            {
                "type": "plan",
                "name": "BTC Plan",
                "status": "running",
                "steps": [
                    {"id": 1, "label": "Read orderbook", "status": "done"},
                    {"id": 2, "label": "Compute RSI", "status": "processing"},
                ],
            },
        )
        await event_emitter(
            "hint",
            {
                "type": "hint",
                "title": "Select strategy",
                "options": [
                    {"id": "scalp", "text": "Scalping"},
                    {"id": "swing", "text": "Swing"},
                ],
            },
        )
        await event_emitter(
            "assistant_delta",
            {
                "type": "assistant_delta",
                "delta": "Partial answer",
            },
        )
        return "Partial answer"


def create_test_client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_agent_chat_stream_returns_sse_events(monkeypatch, tmp_path):
    manager = TemporaryUploadManager(storage_dir=tmp_path, ttl_seconds=3600, max_size_mb=1)
    agent = DummyStreamingAgent()

    monkeypatch.setattr("api.routes.get_upload_manager", lambda: manager)
    monkeypatch.setattr("api.routes.get_agent", lambda scope_id=None, user_id=None: agent)

    client = create_test_client()

    with client.stream(
        "POST",
        "/api/agent/chat/stream",
        json={
            "message": "Stream this plan",
            "scope_id": "user:test",
            "user_id": "user-123",
            "conversation_style": "learning",
            "trading_style": "risk_first",
            "attachment_ids": [],
        },
    ) as response:
        body = "".join(response.iter_text())

    assert response.status_code == 200
    assert "event: thinking_summary" in body
    assert "event: plan" in body
    assert "event: hint" in body
    assert "event: assistant_delta" in body
    assert "event: done" in body
    assert '"status": "completed"' in body
    assert '"conversation_style": "learning"' in body
    assert '"trading_style": "risk_first"' in body
    assert '"intent": {"intent": "plan_or_strategy"' in body
    assert agent.calls[0]["message"] == "Stream this plan"
    assert agent.calls[0]["conversation_style"] == "learning"
    assert agent.calls[0]["trading_style"] == "risk_first"
    assert agent.calls[0]["use_tools"] is True
