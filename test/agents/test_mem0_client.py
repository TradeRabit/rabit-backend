import asyncio

from agents.memory.mem0_client import Mem0Client


class FakeResponse:
    def __init__(self, status=200, json_data=None, text_data="", headers=None):
        self.status = status
        self._json_data = json_data
        self._text_data = text_data
        self.headers = headers or {"content-type": "application/json"}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def json(self):
        return self._json_data

    async def text(self):
        return self._text_data


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.closed = False

    def request(self, method, url, params=None, json=None, headers=None):
        self.calls.append({
            "method": method,
            "url": url,
            "params": params,
            "json": json,
            "headers": headers,
        })
        return self.responses.pop(0)

    def get(self, url, headers=None):
        self.calls.append({
            "method": "GET",
            "url": url,
            "headers": headers,
        })
        return self.responses.pop(0)

    async def close(self):
        self.closed = True


def test_mem0_client_add_memory_uses_oss_payload():
    session = FakeSession([
        FakeResponse(json_data={"id": "mem_1", "memory": "Remember this"}),
    ])
    client = Mem0Client(enabled=True, base_url="http://mem0.test", api_key="secret")
    client.session = session

    result = asyncio.run(
        client.add_memory(
            user_id="user-1",
            text="Remember this",
            metadata={"category": "preference"},
        )
    )

    assert result["id"] == "mem_1"
    call = session.calls[0]
    assert call["method"] == "POST"
    assert call["url"] == "http://mem0.test/memories"
    assert call["json"]["user_id"] == "user-1"
    assert call["json"]["messages"][0]["content"] == "Remember this"
    assert call["json"]["metadata"]["category"] == "preference"
    assert call["headers"]["X-API-Key"] == "secret"


def test_mem0_client_search_and_context_use_search_endpoint():
    session = FakeSession([
        FakeResponse(json_data={"results": [{"id": "mem_1", "memory": "Risk limit is 2%"}]}),
        FakeResponse(json_data={"results": [{"id": "mem_1", "memory": "Risk limit is 2%"}]}),
    ])
    client = Mem0Client(enabled=True, base_url="http://mem0.test")
    client.session = session

    memories = asyncio.run(client.search_memories(user_id="user-1", query="risk", limit=3))
    context = asyncio.run(client.get_context(user_id="user-1", query="risk"))

    assert memories[0]["memory"] == "Risk limit is 2%"
    assert "Risk limit is 2%" in context
    assert session.calls[0]["url"] == "http://mem0.test/search"
    assert session.calls[0]["json"]["query"] == "risk"


def test_mem0_client_lists_deletes_and_checks_health():
    session = FakeSession([
        FakeResponse(json_data={"results": [{"id": "mem_1"}]}),
        FakeResponse(status=204, headers={"content-type": "text/plain"}),
        FakeResponse(status=200, text_data="ok", headers={"content-type": "text/plain"}),
    ])
    client = Mem0Client(enabled=True, base_url="http://mem0.test")
    client.session = session

    memories = asyncio.run(client.get_all_memories(user_id="user-1"))
    deleted = asyncio.run(client.delete_memory(user_id="user-1", memory_id="mem_1"))
    health = asyncio.run(client.health_check())

    assert len(memories) == 1
    assert deleted is True
    assert health["healthy"] is True
    assert session.calls[1]["url"] == "http://mem0.test/memories/mem_1"
    assert session.calls[2]["url"] == "http://mem0.test/"
