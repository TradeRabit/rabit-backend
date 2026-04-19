import asyncio
from pathlib import Path
from types import SimpleNamespace

from agents.backpack_execution import normalize_backpack_execution
from agents.drift_execution import normalize_drift_execution
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
            usage=SimpleNamespace(input_tokens=800, output_tokens=200),
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
                        '"analysis_mode":"technical","analysis_scope":"full_setup",'
                        '"indicator_preference":"indicator_light","need_indicator_confirmation":false,'
                        '"inferred_indicator_hint":"trend indicators",'
                        '"confidence":"high","preferred_tool_groups":["market","research","chart","ui"],'
                        '"routing_reason":"The user asks for analysis",'
                        '"response_language":"english","should_clarify":false,'
                        '"clarification_reason":"","suggested_hint_title":"",'
                        '"suggested_hint_options":[]}'
                    )
                )
            ],
            stop_reason="end_turn",
            usage=SimpleNamespace(input_tokens=120, output_tokens=30),
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


class DummySessionCostService:
    def __init__(self):
        self.calls = []

    def record_usage(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "scope_id": kwargs["scope_id"],
            "user_id": kwargs["user_id"],
            "currency": "USD",
            "total_calls": len(self.calls),
            "total_input_tokens": sum(call["usage"].get("input_tokens", 0) for call in self.calls),
            "total_output_tokens": sum(call["usage"].get("output_tokens", 0) for call in self.calls),
            "total_tokens": sum(
                call["usage"].get("input_tokens", 0) + call["usage"].get("output_tokens", 0)
                for call in self.calls
            ),
            "estimated_cost_usd": 0.00123,
            "model_ids": [kwargs["model_id"]],
            "phases": [],
            "created_at": "2026-04-18T00:00:00+00:00",
            "updated_at": "2026-04-18T00:00:00+00:00",
        }

    def get_scope_summary(self, *, scope_id):
        if not self.calls:
            return None
        latest = self.calls[-1]
        return {
            "scope_id": scope_id,
            "user_id": latest["user_id"],
            "currency": "USD",
            "total_calls": len(self.calls),
            "total_input_tokens": sum(call["usage"].get("input_tokens", 0) for call in self.calls),
            "total_output_tokens": sum(call["usage"].get("output_tokens", 0) for call in self.calls),
            "total_tokens": sum(
                call["usage"].get("input_tokens", 0) + call["usage"].get("output_tokens", 0)
                for call in self.calls
            ),
            "estimated_cost_usd": 0.00123,
            "model_ids": [latest["model_id"]],
            "phases": [],
            "created_at": "2026-04-18T00:00:00+00:00",
            "updated_at": "2026-04-18T00:00:00+00:00",
        }


class DummyMonitoringCostService:
    def get_scope_summary(self, *, scope_id):
        return {
            "scope_id": scope_id,
            "user_id": "wallet:user-1",
            "currency": "USD",
            "alert_setup_cost_usd": 0.001,
            "trigger_cost_usd": 0.0005,
            "monitoring_cost_usd": 0.004,
            "total_cost_usd": 0.0055,
            "alert_setup_count": 1,
            "trigger_count": 1,
            "active_alert_count": 0,
            "active_symbol_count": 0,
            "active_symbols": [],
            "total_symbol_hours": 2.0,
            "created_at": "2026-04-18T00:00:00+00:00",
            "updated_at": "2026-04-18T00:01:00+00:00",
        }


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
    monkeypatch.setattr("agents.backpack_execution.policy.settings.BACKPACK_EXECUTION_ENABLED", True)
    monkeypatch.setattr("agents.drift_execution.policy.settings.DRIFT_EXECUTION_ENABLED", True)

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
            market_context={
                "scope_mode": "locked_asset",
                "symbol": "BTC",
                "timeframe": "4H",
            },
            backpack_execution={
                "enabled": True,
                "exchange": "backpack",
            },
            drift_execution={
                "enabled": False,
                "exchange": "drift",
            },
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
    assert '"enabled": true' in call["system"]
    assert "Backpack live trade execution is enabled for this request." in call["system"]
    assert '- drift_execution: {"enabled": false, "exchange": "drift"}' in call["system"]
    assert "Drift live trade execution is disabled for this request." in call["system"]
    assert agent.last_backpack_execution == normalize_backpack_execution(
        {"enabled": True, "exchange": "backpack"}
    )
    assert agent.last_drift_execution == normalize_drift_execution(
        {"enabled": False, "exchange": "drift"}
    )

    history = agent.get_conversation_history()
    assert history[-2]["role"] == "user"
    assert "chart.png (image/png)" in history[-2]["content"]
    assert "image-bytes" not in history[-2]["content"]


def test_base_agent_builds_document_block(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("agents.core.base.Anthropic", DummyAnthropic)
    monkeypatch.setattr("agents.core.base.AsyncAnthropic", DummyAsyncAnthropic)
    monkeypatch.setattr("agents.core.base.get_mem0_client", lambda: DummyMem0Client())
    monkeypatch.setattr("agents.backpack_execution.policy.settings.BACKPACK_EXECUTION_ENABLED", True)
    monkeypatch.setattr("agents.drift_execution.policy.settings.DRIFT_EXECUTION_ENABLED", True)

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
            market_context={"scope_mode": "global"},
            backpack_execution={"enabled": False, "exchange": "backpack"},
            drift_execution={"enabled": True, "exchange": "drift"},
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
    monkeypatch.setattr("agents.backpack_execution.policy.settings.BACKPACK_EXECUTION_ENABLED", True)
    monkeypatch.setattr("agents.drift_execution.policy.settings.DRIFT_EXECUTION_ENABLED", True)

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
            market_context={
                "scope_mode": "locked_asset",
                "symbol": "SOL",
                "timeframe": "1H",
                "market_state": {
                    "trend_bias": "bullish",
                    "structure_position": "near_support",
                    "summary": "SOL is holding above support.",
                },
            },
            backpack_execution={"enabled": False, "exchange": "backpack"},
            drift_execution={"enabled": True, "exchange": "drift"},
        )
    )

    assert response == "Multimodal response ok"
    call = agent.client.messages.calls[0]
    assert "User prefers SOL trades" in call["system"]
    assert dummy_mem0.calls[0]["user_id"] == "user-99"
    assert "intent: market_analysis" in call["system"]
    assert "user_goal_type: analyze" in call["system"]
    assert "analysis_mode: technical" in call["system"]
    assert "analysis_scope: full_setup" in call["system"]
    assert "indicator_preference: indicator_light" in call["system"]
    assert "inferred_indicator_hint: trend indicators" in call["system"]
    assert "conversation_style: learning" in call["system"]
    assert "trading_style: risk_first" in call["system"]
    assert '"scope_mode": "locked_asset"' in call["system"]
    assert '"symbol": "SOL"' in call["system"]
    assert "SOL is holding above support." in call["system"]
    assert '- backpack_execution: {"enabled": false, "exchange": "backpack"}' in call["system"]
    assert "Backpack live trade execution is disabled for this request." in call["system"]
    assert '- drift_execution: {"enabled": true, "exchange": "drift"}' in call["system"]
    assert "Drift live trade execution is enabled for this request." in call["system"]
    assert "response_language: english" in call["system"]
    assert "should_clarify: false" in call["system"]
    assert agent.last_pipeline_trace is not None
    assert agent.last_pipeline_trace.selected_next_agent == "market_specialist"
    assert agent.last_pipeline_trace.routing_intent == "market_analysis"
    assert "Pipeline node instruction (chart_analysis):" in call["system"]
    assert "Pipeline node instruction (market_snapshot):" in call["system"]


def test_base_agent_tracks_openrouter_session_costs(monkeypatch):
    dummy_costs = DummySessionCostService()
    dummy_monitoring_costs = DummyMonitoringCostService()

    monkeypatch.setattr("agents.core.base.Anthropic", DummyAnthropic)
    monkeypatch.setattr("agents.core.base.AsyncAnthropic", DummyAsyncAnthropic)
    monkeypatch.setattr("agents.core.base.get_mem0_client", lambda: DummyMem0Client())
    monkeypatch.setattr("agents.core.base.get_openrouter_session_cost_service", lambda: dummy_costs)
    monkeypatch.setattr("agents.core.base.get_monitoring_cost_service", lambda: dummy_monitoring_costs)
    monkeypatch.setattr("agents.core.base.settings.USE_OPENROUTER", True)
    monkeypatch.setattr("agents.core.base.settings.OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")

    agent = BaseAgent(
        name="cost-agent",
        system_prompt="You are helpful.",
        scope_id="chat-cost-1",
        user_id="wallet:user-1",
    )

    response = asyncio.run(agent.process("Analyze BTC"))

    assert response == "Multimodal response ok"
    assert [call["phase"] for call in dummy_costs.calls[:2]] == ["intent_router", "response"]
    assert dummy_costs.calls[0]["scope_id"] == "chat-cost-1"
    assert dummy_costs.calls[0]["user_id"] == "wallet:user-1"
    assert agent.last_session_cost_summary is not None
    assert agent.last_session_cost_summary["scope_id"] == "chat-cost-1"
    assert agent.last_service_cost_summary is not None
    assert agent.last_service_cost_summary["model_cost_usd"] == 0.00123
    assert agent.last_service_cost_summary["monitor_cost_usd"] == 0.0055


def test_base_agent_formats_tradingview_screenshot_tool_result(monkeypatch):
    monkeypatch.setattr("agents.core.base.Anthropic", DummyAnthropic)
    monkeypatch.setattr("agents.core.base.AsyncAnthropic", DummyAsyncAnthropic)
    monkeypatch.setattr("agents.core.base.get_mem0_client", lambda: DummyMem0Client())

    agent = BaseAgent(name="tv-agent", system_prompt="You are helpful.")
    content = agent._build_tool_result_content(
        "tv_capture_screenshot",
        {
            "success": True,
            "region": "chart",
            "screenshot_url": "http://localhost:3001/mock-chart.png",
            "agent_image_available": True,
            "agent_image": {
                "content_type": "image/png",
                "data_base64": "aW1hZ2UtYnl0ZXM=",
                "size_bytes": 11,
            },
        },
    )

    assert isinstance(content, list)
    assert content[0]["type"] == "text"
    assert "mock-chart.png" in content[0]["text"]
    assert content[1]["type"] == "image"
    assert content[1]["source"]["media_type"] == "image/png"
    assert content[1]["source"]["data"] == "aW1hZ2UtYnl0ZXM="
