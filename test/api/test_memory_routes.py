from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import router


class DummyMem0Client:
    def __init__(self):
        self.enabled = True
        self.base_url = "http://mem0.test"
        self.calls = []

    async def health_check(self):
        self.calls.append(("health",))
        return {"healthy": True}

    async def get_all_memories(self, user_id):
        self.calls.append(("list", user_id))
        return [{"id": "mem_1", "memory": "Saved preference"}]

    async def search_memories(self, user_id, query, limit=5):
        self.calls.append(("search", user_id, query, limit))
        return [{"id": "mem_1", "memory": "Saved preference"}]

    async def add_memory(self, user_id, text, metadata=None):
        self.calls.append(("add", user_id, text, metadata))
        return {"id": "mem_2", "memory": text}

    async def delete_memory(self, user_id, memory_id):
        self.calls.append(("delete", user_id, memory_id))
        return True

    async def delete_all_memories(self, user_id):
        self.calls.append(("delete_all", user_id))
        return True


def create_test_client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_memory_routes_cover_health_list_search_add_and_delete(monkeypatch):
    dummy_client = DummyMem0Client()
    monkeypatch.setattr("api.routes.get_mem0_client", lambda: dummy_client)

    client = create_test_client()

    health_response = client.get("/api/memory/health")
    list_response = client.get("/api/memory", params={"user_id": "user-1"})
    search_response = client.get(
        "/api/memory/search",
        params={"user_id": "user-1", "query": "preference", "limit": 2},
    )
    add_response = client.post(
        "/api/memory",
        json={
            "user_id": "user-1",
            "text": "Remember I prefer BTC and SOL",
            "metadata": {"category": "preference"},
        },
    )
    delete_response = client.delete("/api/memory/mem_1", params={"user_id": "user-1"})
    delete_all_response = client.delete("/api/memory", params={"user_id": "user-1"})

    assert health_response.status_code == 200
    assert health_response.json()["healthy"] is True

    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    assert search_response.status_code == 200
    assert search_response.json()["query"] == "preference"

    assert add_response.status_code == 200
    assert add_response.json()["success"] is True

    assert delete_response.status_code == 200
    assert delete_response.json()["memory_id"] == "mem_1"

    assert delete_all_response.status_code == 200
    assert delete_all_response.json()["deleted_all"] is True
