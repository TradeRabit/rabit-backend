from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import router


class DummyConversationDatabase:
    def __init__(self):
        self.data = {
            "assist-asset-BTC-1": {
                "scope_id": "assist-asset-BTC-1",
                "messages": [
                    {
                        "role": "user",
                        "content": "Analyze BTC today",
                        "timestamp": "2026-04-21T10:00:00+00:00",
                    },
                    {
                        "role": "assistant",
                        "content": "BTC looks constructive.",
                        "timestamp": "2026-04-21T10:00:05+00:00",
                    },
                ],
                "metadata": {
                    "created_at": "2026-04-21T10:00:00+00:00",
                    "user_id": "wallet:user-1",
                    "title": "BTC Assist",
                    "scope_mode": "locked_asset",
                    "symbol": "BTC",
                    "exchange": "backpack",
                    "source_screen": "asset_detail_assist",
                },
                "updated_at": "2026-04-21T10:00:05+00:00",
            },
            "assist-global-2": {
                "scope_id": "assist-global-2",
                "messages": [
                    {
                        "role": "user",
                        "content": "Scan market",
                        "timestamp": "2026-04-20T10:00:00+00:00",
                    },
                ],
                "metadata": {
                    "created_at": "2026-04-20T10:00:00+00:00",
                    "user_id": "wallet:someone-else",
                    "title": "Other Wallet",
                },
                "updated_at": "2026-04-20T10:00:00+00:00",
            },
        }

    def build_session_summary(self, scope_id, session_data):
        metadata = session_data.get("metadata", {})
        messages = session_data.get("messages", [])
        return {
            "scope_id": scope_id,
            "title": metadata.get("title", "Untitled"),
            "message_count": len(messages),
            "created_at": metadata.get("created_at"),
            "updated_at": session_data.get("updated_at"),
            "last_message": messages[-1]["content"] if messages else None,
            "user_id": metadata.get("user_id"),
            "scope_mode": metadata.get("scope_mode"),
            "symbol": metadata.get("symbol"),
            "exchange": metadata.get("exchange"),
            "source_screen": metadata.get("source_screen"),
        }

    def list_sessions(self, user_id=None):
        return [
            self.build_session_summary(scope_id, session)
            for scope_id, session in self.data.items()
            if not user_id or session.get("metadata", {}).get("user_id") == user_id
        ]

    def get_session_record(self, scope_id):
        return self.data.get(scope_id)

    def update_session_metadata(self, scope_id, metadata):
        if scope_id in self.data:
            self.data[scope_id]["metadata"].update(metadata)

    def delete_session(self, scope_id):
        self.data.pop(scope_id, None)


def create_test_client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def build_auth_header(monkeypatch):
    monkeypatch.setattr(
        "api.routes.verify_access_token",
        lambda token: {
            "sub": "wallet-address",
            "user_id": "wallet:user-1",
            "wallet_address": "wallet-address",
        },
    )
    return {"Authorization": "Bearer token"}


def test_agent_session_routes_support_list_detail_rename_delete(monkeypatch):
    database = DummyConversationDatabase()
    monkeypatch.setattr("api.routes.get_conversation_database", lambda: database)

    client = create_test_client()
    headers = build_auth_header(monkeypatch)

    list_response = client.get("/api/agent/sessions", headers=headers)
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload["total"] == 1
    assert list_payload["sessions"][0]["scope_id"] == "assist-asset-BTC-1"
    assert list_payload["sessions"][0]["title"] == "BTC Assist"

    detail_response = client.get("/api/agent/sessions/assist-asset-BTC-1", headers=headers)
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["symbol"] == "BTC"
    assert len(detail_payload["messages"]) == 2
    assert detail_payload["messages"][0]["content"] == "Analyze BTC today"

    rename_response = client.patch(
        "/api/agent/sessions/assist-asset-BTC-1",
        headers=headers,
        json={"title": "Renamed BTC Session"},
    )
    assert rename_response.status_code == 200
    assert rename_response.json()["title"] == "Renamed BTC Session"

    delete_response = client.delete("/api/agent/sessions/assist-asset-BTC-1", headers=headers)
    assert delete_response.status_code == 200
    assert delete_response.json() == {"success": True, "scope_id": "assist-asset-BTC-1"}

    list_after_delete = client.get("/api/agent/sessions", headers=headers)
    assert list_after_delete.status_code == 200
    assert list_after_delete.json()["total"] == 0


def test_agent_session_routes_reject_other_user_session(monkeypatch):
    database = DummyConversationDatabase()
    monkeypatch.setattr("api.routes.get_conversation_database", lambda: database)

    client = create_test_client()
    headers = build_auth_header(monkeypatch)

    response = client.get("/api/agent/sessions/assist-global-2", headers=headers)
    assert response.status_code == 403
