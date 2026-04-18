from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import router


class DummyExchangeConnectionService:
    def __init__(self):
        self.created = []
        self.updated = []
        self.deleted = []
        self.records = {
            "conn-1": {
                "id": "conn-1",
                "user_id": "user-1",
                "exchange": "backpack",
                "label": "Primary",
                "last4": "1234",
                "fingerprint": "abc123",
                "trading_enabled": True,
                "read_only": False,
                "is_active": True,
                "created_at": "2026-04-18T00:00:00+00:00",
                "updated_at": "2026-04-18T00:00:00+00:00",
                "last_used_at": None,
                "revoked_at": None,
            }
        }

    def create_connection(self, **kwargs):
        self.created.append(kwargs)
        return self.records["conn-1"]

    def list_connections(self, **kwargs):
        return list(self.records.values())

    def update_connection(self, **kwargs):
        self.updated.append(kwargs)
        updated = dict(self.records["conn-1"])
        if kwargs.get("label") is not None:
            updated["label"] = kwargs["label"]
        if kwargs.get("trading_enabled") is not None:
            updated["trading_enabled"] = kwargs["trading_enabled"]
        if kwargs.get("read_only") is not None:
            updated["read_only"] = kwargs["read_only"]
        if kwargs.get("is_active") is not None:
            updated["is_active"] = kwargs["is_active"]
        self.records["conn-1"] = updated
        return updated

    def delete_connection(self, **kwargs):
        self.deleted.append(kwargs)
        return {
            "success": True,
            "connection_id": kwargs["connection_id"],
            "user_id": kwargs["user_id"],
            "exchange": "backpack",
        }


def create_test_client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_exchange_connection_routes(monkeypatch):
    service = DummyExchangeConnectionService()
    monkeypatch.setattr("api.routes.get_exchange_connection_service", lambda: service)

    client = create_test_client()

    create_response = client.post(
        "/api/exchange-connections/backpack",
        json={
            "user_id": "user-1",
            "label": "Primary",
            "api_key": "public-key",
            "api_secret": "private-secret",
            "trading_enabled": True,
            "read_only": False,
            "is_active": True,
        },
    )
    assert create_response.status_code == 200
    assert create_response.json()["id"] == "conn-1"
    assert service.created[0]["user_id"] == "user-1"
    assert service.created[0]["exchange"] == "backpack"

    list_response = client.get("/api/exchange-connections", params={"user_id": "user-1"})
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1
    assert list_response.json()["connections"][0]["label"] == "Primary"
    assert "api_secret" not in list_response.text

    update_response = client.patch(
        "/api/exchange-connections/conn-1",
        json={
            "user_id": "user-1",
            "label": "Primary Updated",
            "trading_enabled": False,
            "read_only": True,
            "is_active": True,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["label"] == "Primary Updated"
    assert service.updated[0]["connection_id"] == "conn-1"

    delete_response = client.delete(
        "/api/exchange-connections/conn-1",
        params={"user_id": "user-1"},
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["success"] is True
    assert service.deleted[0]["connection_id"] == "conn-1"
