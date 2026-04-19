import asyncio
from types import SimpleNamespace

from agents.core.base import AgentExecutionError, BaseAgent


class FailingMessagesAPI:
    def create(self, **kwargs):
        raise RuntimeError("database password leaked in raw error")


class FailingAnthropic:
    def __init__(self, *args, **kwargs):
        self.messages = FailingMessagesAPI()


class DummyAsyncMessagesAPI:
    async def create(self, **kwargs):
        return SimpleNamespace(
            content=[
                SimpleNamespace(
                    text=(
                        '{"intent":"broker_execution","user_goal_type":"execution_prep",'
                        '"goal_summary":"Prepare execution",'
                        '"analysis_mode":"operational","analysis_scope":"risk_review",'
                        '"indicator_preference":"auto","need_indicator_confirmation":false,'
                        '"inferred_indicator_hint":"","confidence":"high",'
                        '"preferred_tool_groups":["execution","ui"],'
                        '"routing_reason":"Execution workflow requested.",'
                        '"response_language":"english","should_clarify":false,'
                        '"clarification_reason":"","suggested_hint_title":"",'
                        '"suggested_hint_options":[]}'
                    )
                )
            ],
            usage=SimpleNamespace(input_tokens=10, output_tokens=5),
        )


class DummyAsyncAnthropic:
    def __init__(self, *args, **kwargs):
        self.messages = DummyAsyncMessagesAPI()


class DummyMem0Client:
    async def get_context(self, user_id, query):
        return ""


async def _noop_emitter(event_name, payload):
    return None


def test_base_agent_process_returns_safe_fallback(monkeypatch):
    monkeypatch.setattr("agents.core.base.Anthropic", FailingAnthropic)
    monkeypatch.setattr("agents.core.base.AsyncAnthropic", DummyAsyncAnthropic)
    monkeypatch.setattr("agents.core.base.get_mem0_client", lambda: DummyMem0Client())

    agent = BaseAgent(name="TradingAgent", system_prompt="You are helpful.")

    response = asyncio.run(agent.process("Place the order now"))

    assert "database password leaked" not in response
    assert "execution workflow" in response.lower()
    assert agent.last_pipeline_trace is not None
    assert agent.last_pipeline_trace.fallback_mode == "safe_error_response"
    assert agent.last_pipeline_trace.final_status == "degraded"


def test_base_agent_process_stream_raises_safe_error(monkeypatch):
    monkeypatch.setattr("agents.core.base.Anthropic", FailingAnthropic)
    monkeypatch.setattr("agents.core.base.AsyncAnthropic", DummyAsyncAnthropic)
    monkeypatch.setattr("agents.core.base.get_mem0_client", lambda: DummyMem0Client())

    agent = BaseAgent(name="TradingAgent", system_prompt="You are helpful.")

    try:
        asyncio.run(
            agent.process_stream(
                "Place the order now",
                event_emitter=_noop_emitter,
            )
        )
    except AgentExecutionError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected AgentExecutionError")

    assert "database password leaked" not in message
    assert "execution workflow" in message.lower()
    assert agent.last_pipeline_trace is not None
    assert agent.last_pipeline_trace.fallback_mode == "safe_stream_error"
    assert agent.last_pipeline_trace.final_status == "failed"
