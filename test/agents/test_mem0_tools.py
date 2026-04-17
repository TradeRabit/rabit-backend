import asyncio

from agents.tools.core.runtime_context import reset_current_user_id, set_current_user_id
from agents.tools.memory.mem0_tools import add_user_memory, delete_user_memory, get_user_memory


class DummyMem0Client:
    def __init__(self):
        self.calls = []

    async def add_memory(self, user_id, text, metadata=None):
        self.calls.append(("add", user_id, text, metadata))
        return {"id": "mem_1", "memory": text}

    async def search_memories(self, user_id, query, limit=5):
        self.calls.append(("search", user_id, query, limit))
        return [{"id": "mem_1", "memory": "Saved risk limit"}]

    async def delete_memory(self, user_id, memory_id):
        self.calls.append(("delete", user_id, memory_id))
        return True


def test_mem0_tools_use_active_user_id(monkeypatch):
    dummy_client = DummyMem0Client()
    monkeypatch.setattr("agents.tools.memory.mem0_tools.get_mem0_client", lambda: dummy_client)

    token = set_current_user_id("user-42")
    try:
        add_result = asyncio.run(
            add_user_memory(
                text="My maximum risk is 2%",
                category="risk",
                metadata_json='{"source":"chat"}',
            )
        )
        get_result = asyncio.run(get_user_memory(query="risk", limit=3))
        delete_result = asyncio.run(delete_user_memory("mem_1"))
    finally:
        reset_current_user_id(token)

    assert add_result["success"] is True
    assert add_result["user_id"] == "user-42"
    assert get_result["total"] == 1
    assert delete_result["memory_id"] == "mem_1"
    assert dummy_client.calls[0] == (
        "add",
        "user-42",
        "My maximum risk is 2%",
        {"source": "chat", "category": "risk"},
    )
    assert dummy_client.calls[1] == ("search", "user-42", "risk", 3)
    assert dummy_client.calls[2] == ("delete", "user-42", "mem_1")
