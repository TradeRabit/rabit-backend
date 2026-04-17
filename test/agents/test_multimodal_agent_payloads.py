import asyncio
from pathlib import Path
from types import SimpleNamespace

from agents.core.base import BaseAgent
from agents.uploads import AgentAttachment


class DummyMessagesAPI:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            content=[SimpleNamespace(text="Multimodal response ok")],
            stop_reason="end_turn",
        )


class DummyAnthropic:
    def __init__(self, *args, **kwargs):
        self.messages = DummyMessagesAPI()


class DummyAsyncMessagesAPI:
    def __init__(self):
        self.calls = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            content=[
                SimpleNamespace(
                    text=(
                        '{"intent":"market_analysis","user_goal_type":"analyze","goal_summary":"Analyze the user request",'
                        '"confidence":"high","preferred_tool_groups":["market","research","chart","ui"],'
                        '"routing_reason":"The user asks for analysis",'
                        '"response_language":"english","should_clarify":false,'
                        '"clarification_reason":"","suggested_hint_title":"",'
                        '"suggested_hint_options":[]}'
                    )
                )
            ],
            stop_reason="end_turn",
        )


class DummyAsyncAnthropic:
    def __init__(self, *args, **kwargs):
        self.messages = DummyAsyncMessagesAPI()


class DummyMem0Client:
    def __init__(self, context=""):
        self.context = context
        self.calls = []

    async def get_context(self, user_id, query):
        self.calls.append({"user_id": user_id, "query": query})
        return self.context


def make_attachment(tmp_path: Path, filename: str, content_type: str, kind: str, payload: bytes):
    file_path = tmp_path / filename
    file_path.write_bytes(payload)
    return AgentAttachment(
        file_id=f"{filename}-id",
        filename=filename,
        content_type=content_type,
        kind=kind,
        path=str(file_path),
        size_bytes=len(payload),
    )


def test_base_agent_builds_multimodal_payload_and_memory_summary(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("agents.core.base.Anthropic", DummyAnthropic)
    monkeypatch.setattr("agents.core.base.AsyncAnthropic", DummyAsyncAnthropic)
    monkeypatch.setattr("agents.core.base.get_mem0_client", lambda: DummyMem0Client())

    agent = BaseAgent(name="test-agent", system_prompt="You are helpful.")
    attachment = make_attachment(
        tmp_path,
        "chart.png",
        "image/png",
        "image",
        b"image-bytes",
    )

    response = asyncio.run(
        agent.process(
            "Analyze this chart",
            attachments=[attachment],
            conversation_style="concise",
            trading_style="trend_following",
        )
    )

    assert response == "Multimodal response ok"
    call = agent.client.messages.calls[0]
    user_message = call["messages"][-1]

    assert user_message["role"] == "user"
    assert isinstance(user_message["content"], list)
    assert user_message["content"][0]["type"] == "text"
    assert user_message["content"][1]["type"] == "image"
    assert user_message["content"][1]["source"]["media_type"] == "image/png"

    history = agent.get_conversation_history()
    assert history[-2]["role"] == "user"
    assert "chart.png (image/png)" in history[-2]["content"]
    assert "image-bytes" not in history[-2]["content"]


def test_base_agent_builds_document_block(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("agents.core.base.Anthropic", DummyAnthropic)
    monkeypatch.setattr("agents.core.base.AsyncAnthropic", DummyAsyncAnthropic)
    monkeypatch.setattr("agents.core.base.get_mem0_client", lambda: DummyMem0Client())

    agent = BaseAgent(name="doc-agent", system_prompt="You are helpful.")
    attachment = make_attachment(
        tmp_path,
        "report.pdf",
        "application/pdf",
        "document",
        b"%PDF-1.4",
    )

    response = asyncio.run(
        agent.process(
            "Summarize this report",
            attachments=[attachment],
            conversation_style="formal",
            trading_style="systematic",
        )
    )

    assert response == "Multimodal response ok"
    call = agent.client.messages.calls[0]
    doc_block = call["messages"][-1]["content"][1]
    assert doc_block["type"] == "document"
    assert doc_block["source"]["media_type"] == "application/pdf"


def test_base_agent_injects_mem0_context_into_system_prompt(monkeypatch):
    monkeypatch.setattr("agents.core.base.Anthropic", DummyAnthropic)
    monkeypatch.setattr("agents.core.base.AsyncAnthropic", DummyAsyncAnthropic)
    dummy_mem0 = DummyMem0Client("Relevant long-term user memory:\n- User prefers SOL trades")
    monkeypatch.setattr("agents.core.base.get_mem0_client", lambda: dummy_mem0)

    agent = BaseAgent(
        name="memory-agent",
        system_prompt="You are helpful.",
        user_id="user-99",
    )

    response = asyncio.run(
        agent.process(
            "What should I trade today?",
            conversation_style="learning",
            trading_style="risk_first",
        )
    )

    assert response == "Multimodal response ok"
    call = agent.client.messages.calls[0]
    assert "User prefers SOL trades" in call["system"]
    assert dummy_mem0.calls[0]["user_id"] == "user-99"
    assert "intent: market_analysis" in call["system"]
    assert "user_goal_type: analyze" in call["system"]
    assert "conversation_style: learning" in call["system"]
    assert "trading_style: risk_first" in call["system"]
    assert "response_language: english" in call["system"]
    assert "should_clarify: false" in call["system"]
