import asyncio
from types import SimpleNamespace

from agents.core.base import BaseAgent
from agents.core.pipeline import (
    PIPELINE_NODE_CLARIFICATION_PREP,
    PIPELINE_NODE_CHART_ANALYSIS,
    PIPELINE_NODE_EXECUTION_SNAPSHOT,
    PIPELINE_NODE_GENERAL_FALLBACK,
    PIPELINE_NODE_MEMORY_SNAPSHOT,
    PIPELINE_NODE_MARKET_SNAPSHOT,
    PIPELINE_NODE_PORTFOLIO_SNAPSHOT,
    PIPELINE_NODE_RESEARCH_SNAPSHOT,
    PIPELINE_NODE_RESPONSE_COMPOSER,
    SPECIALIST_TARGET_CLARIFICATION,
    SPECIALIST_TARGET_EXECUTION,
    SPECIALIST_TARGET_GENERAL,
    SPECIALIST_TARGET_MARKET,
    SPECIALIST_TARGET_MEMORY,
    SPECIALIST_TARGET_PORTFOLIO,
    SPECIALIST_TARGET_RESEARCH,
    build_pipeline_nodes,
    build_pipeline_trace,
    resolve_specialist_target,
)
from agents.intent_router import AgentIntentContext
from agents.tools_registry import register_trading_tools


class DummyMessagesAPI:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            content=[SimpleNamespace(text="Pipeline response ok")],
            stop_reason="end_turn",
            usage=SimpleNamespace(input_tokens=50, output_tokens=20),
        )


class DummyAnthropic:
    def __init__(self, *args, **kwargs):
        self.messages = DummyMessagesAPI()


class DummyAsyncMessagesAPI:
    async def create(self, **kwargs):
        return SimpleNamespace(
            content=[
                SimpleNamespace(
                    text=(
                        '{"intent":"broker_execution","user_goal_type":"execution_prep",'
                        '"goal_summary":"Prepare an execution flow",'
                        '"analysis_mode":"operational","analysis_scope":"risk_review",'
                        '"indicator_preference":"auto","need_indicator_confirmation":false,'
                        '"inferred_indicator_hint":"","confidence":"high",'
                        '"preferred_tool_groups":["execution","portfolio","ui"],'
                        '"routing_reason":"The user is preparing or managing an execution workflow.",'
                        '"response_language":"english","should_clarify":false,'
                        '"clarification_reason":"","suggested_hint_title":"",'
                        '"suggested_hint_options":[]}'
                    )
                )
            ],
            usage=SimpleNamespace(input_tokens=30, output_tokens=15),
        )


class DummyAsyncAnthropic:
    def __init__(self, *args, **kwargs):
        self.messages = DummyAsyncMessagesAPI()


class DummyMem0Client:
    async def get_context(self, user_id, query):
        return ""


def test_resolve_specialist_target_maps_intents():
    assert resolve_specialist_target(AgentIntentContext(intent="market_analysis", confidence="high")) == SPECIALIST_TARGET_MARKET
    assert resolve_specialist_target(AgentIntentContext(intent="broker_execution", confidence="high")) == SPECIALIST_TARGET_EXECUTION
    assert resolve_specialist_target(AgentIntentContext(intent="portfolio_review", confidence="high")) == SPECIALIST_TARGET_PORTFOLIO
    assert resolve_specialist_target(AgentIntentContext(intent="memory_lookup", confidence="high")) == SPECIALIST_TARGET_MEMORY
    assert resolve_specialist_target(AgentIntentContext(intent="research", confidence="high")) == SPECIALIST_TARGET_RESEARCH


def test_resolve_specialist_target_falls_back_for_low_confidence_and_clarification():
    low_confidence = AgentIntentContext(intent="market_analysis", confidence="low")
    clarify = AgentIntentContext(intent="trade_setup", confidence="high", should_clarify=True)

    assert resolve_specialist_target(low_confidence) == SPECIALIST_TARGET_GENERAL
    assert resolve_specialist_target(clarify) == SPECIALIST_TARGET_CLARIFICATION


def test_build_pipeline_trace_is_serializable_and_marks_fallback():
    context = AgentIntentContext(
        intent="general_chat",
        confidence="low",
        should_clarify=False,
        routing_reason="Router fallback",
    )

    trace = build_pipeline_trace(entry_agent="TradingAgent", intent_context=context)
    dumped = trace.model_dump()

    assert dumped["entry_agent"] == "TradingAgent"
    assert dumped["selected_next_agent"] == SPECIALIST_TARGET_GENERAL
    assert dumped["fallback_mode"] == "low_confidence_route"
    assert dumped["routing_intent"] == "general_chat"
    assert dumped["pipeline_nodes"] == [
        {
            "name": PIPELINE_NODE_GENERAL_FALLBACK,
            "status": "planned",
            "summary": "Prepare a safer low-confidence fallback mode before the main answer.",
            "instruction": (
                "Act as a general-fallback specialist step. Focus on uncertainty-aware behavior, avoid "
                "over-committing, and prepare the final runtime to answer safely when routing confidence is low."
            ),
            "config": {
                "llm_allowed_tool_names": [
                    "show_hint",
                    "show_plan",
                    "show_thinking_summary",
                ],
            },
            "metadata": {},
        },
        {
            "name": PIPELINE_NODE_RESPONSE_COMPOSER,
            "status": "planned",
            "summary": "Use the accumulated node observations when forming the final response.",
            "instruction": "",
            "config": {},
            "metadata": {},
        }
    ]


def test_build_pipeline_nodes_plans_general_and_clarification_paths():
    low_confidence_nodes = build_pipeline_nodes(
        intent_context=AgentIntentContext(intent="market_analysis", confidence="low"),
        user_input="Analyze this market",
    )
    clarification_nodes = build_pipeline_nodes(
        intent_context=AgentIntentContext(
            intent="trade_setup",
            confidence="high",
            should_clarify=True,
            preferred_tool_groups=["chart", "ui"],
            suggested_hint_title="Which asset?",
            suggested_hint_options=[{"id": "btc", "text": "BTC"}, {"id": "sol", "text": "SOL"}],
        ),
        user_input="Check setup",
    )

    assert [node.name for node in low_confidence_nodes] == [
        PIPELINE_NODE_GENERAL_FALLBACK,
        PIPELINE_NODE_RESPONSE_COMPOSER,
    ]
    assert [node.name for node in clarification_nodes] == [
        PIPELINE_NODE_CLARIFICATION_PREP,
        PIPELINE_NODE_RESPONSE_COMPOSER,
    ]
    assert clarification_nodes[0].config["llm_allowed_tool_names"] == ["show_hint"]
    assert low_confidence_nodes[0].config["llm_allowed_tool_names"] == [
        "show_hint",
        "show_plan",
        "show_thinking_summary",
    ]


def test_build_pipeline_nodes_keeps_low_confidence_chart_requests_in_safe_mode():
    nodes = build_pipeline_nodes(
        intent_context=AgentIntentContext(
            intent="market_analysis",
            confidence="low",
            preferred_tool_groups=["market", "chart", "ui"],
            indicator_preference="indicator_light",
        ),
        user_input="Analyze the BTC chart with RSI and MACD",
    )

    assert [node.name for node in nodes] == [
        PIPELINE_NODE_GENERAL_FALLBACK,
        PIPELINE_NODE_RESPONSE_COMPOSER,
    ]

    write_nodes = build_pipeline_nodes(
        intent_context=AgentIntentContext(
            intent="trade_setup",
            confidence="low",
            preferred_tool_groups=["market", "chart", "ui"],
        ),
        user_input="Mark support at 65000 on BTC and clear drawings",
    )

    assert [node.name for node in write_nodes] == [
        PIPELINE_NODE_GENERAL_FALLBACK,
        PIPELINE_NODE_RESPONSE_COMPOSER,
    ]


def test_build_pipeline_nodes_plans_chart_analysis_for_chart_requests():
    context = AgentIntentContext(
        intent="market_analysis",
        confidence="high",
        analysis_mode="technical",
        preferred_tool_groups=["market", "chart", "ui"],
        indicator_preference="indicator_light",
    )

    nodes = build_pipeline_nodes(
        intent_context=context,
        user_input="Analyze the BTC chart with RSI and MACD",
    )

    assert [node.name for node in nodes] == [
        PIPELINE_NODE_CHART_ANALYSIS,
        PIPELINE_NODE_MARKET_SNAPSHOT,
        PIPELINE_NODE_RESPONSE_COMPOSER,
    ]
    assert nodes[0].instruction.startswith("Act as a chart-analysis specialist step.")
    assert nodes[0].config["chart_mode"] == "analysis"
    assert nodes[0].config["allow_chart_write"] is False
    assert nodes[0].config["max_steps"] == 4
    assert nodes[1].config["max_headlines"] == 3


def test_build_pipeline_nodes_enables_write_mode_for_chart_write_requests():
    context = AgentIntentContext(
        intent="trade_setup",
        confidence="high",
        preferred_tool_groups=["market", "chart", "ui"],
    )

    nodes = build_pipeline_nodes(
        intent_context=context,
        user_input="Clear drawings and mark support at 65000 on BTC 4h",
    )

    assert [node.name for node in nodes] == [
        PIPELINE_NODE_CHART_ANALYSIS,
        PIPELINE_NODE_MARKET_SNAPSHOT,
        PIPELINE_NODE_RESPONSE_COMPOSER,
    ]
    assert nodes[0].config["chart_mode"] == "write"
    assert nodes[0].config["allow_chart_write"] is True
    assert nodes[0].config["capture_screenshot_after_write"] is True
    assert nodes[0].config["llm_allowed_tool_names"] == [
        "show_hint",
        "show_plan",
        "show_thinking_summary",
    ]


def test_build_pipeline_nodes_plans_research_snapshot_for_research_requests():
    context = AgentIntentContext(
        intent="macro_context",
        confidence="high",
        preferred_tool_groups=["research", "market", "ui"],
    )

    nodes = build_pipeline_nodes(
        intent_context=context,
        user_input="What is the macro context today?",
    )

    assert [node.name for node in nodes] == [
        PIPELINE_NODE_MARKET_SNAPSHOT,
        PIPELINE_NODE_RESEARCH_SNAPSHOT,
        PIPELINE_NODE_RESPONSE_COMPOSER,
    ]
    assert nodes[1].config["max_search_results"] == 3


def test_build_pipeline_nodes_plans_portfolio_execution_and_memory_snapshots():
    portfolio_nodes = build_pipeline_nodes(
        intent_context=AgentIntentContext(intent="portfolio_review", confidence="high", preferred_tool_groups=["portfolio", "ui"]),
        user_input="Review my portfolio",
    )
    execution_nodes = build_pipeline_nodes(
        intent_context=AgentIntentContext(intent="broker_execution", confidence="high", preferred_tool_groups=["execution", "portfolio", "ui"]),
        user_input="Check execution readiness",
    )
    memory_nodes = build_pipeline_nodes(
        intent_context=AgentIntentContext(intent="memory_lookup", confidence="high", preferred_tool_groups=["memory", "ui"]),
        user_input="What do you remember about my style?",
    )

    assert [node.name for node in portfolio_nodes] == [PIPELINE_NODE_PORTFOLIO_SNAPSHOT, PIPELINE_NODE_RESPONSE_COMPOSER]
    assert [node.name for node in execution_nodes] == [PIPELINE_NODE_EXECUTION_SNAPSHOT, PIPELINE_NODE_RESPONSE_COMPOSER]
    assert [node.name for node in memory_nodes] == [PIPELINE_NODE_MEMORY_SNAPSHOT, PIPELINE_NODE_RESPONSE_COMPOSER]


def test_effective_allowed_tool_names_respects_node_allow_and_block_lists(monkeypatch):
    monkeypatch.setattr("agents.core.base.Anthropic", DummyAnthropic)
    monkeypatch.setattr("agents.core.base.AsyncAnthropic", DummyAsyncAnthropic)
    monkeypatch.setattr("agents.core.base.get_mem0_client", lambda: DummyMem0Client())

    agent = BaseAgent(name="TradingAgent", system_prompt="You are helpful.")

    chart_context = AgentIntentContext(
        intent="market_analysis",
        confidence="high",
        preferred_tool_groups=["market", "chart", "ui"],
        indicator_preference="indicator_light",
    )
    agent.last_pipeline_trace = build_pipeline_trace(
        entry_agent="TradingAgent",
        intent_context=chart_context,
        user_input="Analyze the BTC chart with RSI",
    )

    effective_chart_tools = agent._get_effective_allowed_tool_names(chart_context)
    assert effective_chart_tools is not None
    assert "tv_get_state" in effective_chart_tools
    assert "tv_add_indicator" in effective_chart_tools
    assert "show_hint" in effective_chart_tools
    assert "tv_draw_line" not in effective_chart_tools
    assert "tv_draw_horizontal_line" not in effective_chart_tools
    assert "tv_create_alert" not in effective_chart_tools
    assert "tv_delete_alert" not in effective_chart_tools

    clarification_context = AgentIntentContext(
        intent="trade_setup",
        confidence="high",
        should_clarify=True,
    )
    agent.last_pipeline_trace = build_pipeline_trace(
        entry_agent="TradingAgent",
        intent_context=clarification_context,
        user_input="Check setup",
    )

    assert agent._get_effective_allowed_tool_names(clarification_context) == {"show_hint"}

    write_context = AgentIntentContext(
        intent="trade_setup",
        confidence="high",
        preferred_tool_groups=["market", "chart", "ui"],
    )
    agent.last_pipeline_trace = build_pipeline_trace(
        entry_agent="TradingAgent",
        intent_context=write_context,
        user_input="Clear drawings and mark support at 65000 on BTC",
    )

    assert agent._get_effective_allowed_tool_names(write_context) == {
        "show_hint",
        "show_plan",
        "show_thinking_summary",
    }


def test_base_agent_tracks_pipeline_trace(monkeypatch):
    monkeypatch.setattr("agents.core.base.Anthropic", DummyAnthropic)
    monkeypatch.setattr("agents.core.base.AsyncAnthropic", DummyAsyncAnthropic)
    monkeypatch.setattr("agents.core.base.get_mem0_client", lambda: DummyMem0Client())

    agent = BaseAgent(name="TradingAgent", system_prompt="You are helpful.")

    response = asyncio.run(agent.process("Help me prepare execution"))

    assert response == "Pipeline response ok"
    assert agent.last_pipeline_trace is not None
    assert agent.last_pipeline_trace.selected_next_agent == SPECIALIST_TARGET_EXECUTION
    assert agent.last_pipeline_trace.routing_intent == "broker_execution"
    assert agent.last_pipeline_trace.final_status == "completed"


def test_base_agent_executes_chart_pipeline_nodes(monkeypatch):
    monkeypatch.setattr("agents.core.base.Anthropic", DummyAnthropic)
    monkeypatch.setattr("agents.core.base.AsyncAnthropic", DummyAsyncAnthropic)
    monkeypatch.setattr("agents.core.base.get_mem0_client", lambda: DummyMem0Client())
    register_trading_tools()

    async def fake_route_intent(self, user_input, history, market_context=None):
        return AgentIntentContext(
            intent="market_analysis",
            confidence="high",
            analysis_mode="technical",
            preferred_tool_groups=["market", "chart", "ui"],
            indicator_preference="indicator_light",
            inferred_indicator_hint="RSI",
        )

    state = {"symbol": "BTC", "timeframe": "60", "indicators": []}
    calls = []

    async def fake_execute(name, arguments):
        calls.append(name)
        if name == "tv_get_state":
            return SimpleNamespace(success=True, data={"data": dict(state)}, error=None)
        if name == "tv_add_indicator":
            state["indicators"].append({"name": arguments["indicator"], "entity_id": "rsi-1"})
            return SimpleNamespace(success=True, data={"entity_id": "rsi-1"}, error=None)
        if name == "tv_get_quote":
            return SimpleNamespace(success=True, data={"data": {"symbol": "BTC", "price": 65000}}, error=None)
        if name == "tv_get_indicator_values":
            return SimpleNamespace(success=True, data={"data": {"RSI": 61.5}}, error=None)
        if name == "get_price":
            return SimpleNamespace(
                success=True,
                data={"success": True, "symbol": "BTC", "price": 65000, "change_24h": 2.1},
                error=None,
            )
        if name == "search_news_by_symbols":
            return SimpleNamespace(
                success=True,
                data={
                    "success": True,
                    "results": {
                        "BTC": [
                            {
                                "title": "Bitcoin reclaims momentum",
                                "source": "MockWire",
                                "date": "2026-04-19T00:00:00+00:00",
                                "detected_at": "2026-04-19T00:05:00+00:00",
                                "is_new": True,
                            }
                        ]
                    },
                },
                error=None,
            )
        raise AssertionError(f"Unexpected tool call: {name}")

    monkeypatch.setattr(BaseAgent, "_route_intent", fake_route_intent)
    monkeypatch.setattr("agents.core.base.tool_registry.execute", fake_execute)

    agent = BaseAgent(name="TradingAgent", system_prompt="You are helpful.")

    response = asyncio.run(agent.process("Analyze the BTC chart with RSI", use_tools=True))

    assert response == "Pipeline response ok"
    assert agent.last_pipeline_trace is not None
    assert agent.last_pipeline_trace.selected_next_agent == SPECIALIST_TARGET_MARKET
    assert [node.name for node in agent.last_pipeline_trace.pipeline_nodes] == [
        PIPELINE_NODE_CHART_ANALYSIS,
        PIPELINE_NODE_MARKET_SNAPSHOT,
        PIPELINE_NODE_RESPONSE_COMPOSER,
    ]
    assert agent.last_pipeline_trace.pipeline_nodes[0].status == "completed"
    assert agent.last_pipeline_trace.pipeline_nodes[1].status == "completed"
    assert "tv_add_indicator" in calls
    assert "get_price" in calls
    assert "search_news_by_symbols" in calls
    assert "tv_draw_line" not in calls
    assert "Pipeline node instruction (chart_analysis):" in agent.client.messages.calls[0]["system"]
    assert "Pipeline node instruction (market_snapshot):" in agent.client.messages.calls[0]["system"]
    tool_names = {tool["name"] for tool in agent.client.messages.calls[0]["tools"]}
    assert "tv_draw_line" not in tool_names
    assert "tv_draw_horizontal_line" not in tool_names
    assert "tv_create_alert" not in tool_names
    assert "tv_delete_alert" not in tool_names
    assert "tv_get_state" in tool_names
    assert "tv_add_indicator" in tool_names


def test_base_agent_executes_chart_write_inside_same_node(monkeypatch):
    monkeypatch.setattr("agents.core.base.Anthropic", DummyAnthropic)
    monkeypatch.setattr("agents.core.base.AsyncAnthropic", DummyAsyncAnthropic)
    monkeypatch.setattr("agents.core.base.get_mem0_client", lambda: DummyMem0Client())
    register_trading_tools()

    async def fake_route_intent(self, user_input, history, market_context=None):
        return AgentIntentContext(
            intent="trade_setup",
            confidence="high",
            preferred_tool_groups=["market", "chart", "ui"],
        )

    state = {"symbol": "BTC", "timeframe": "60", "indicators": []}
    calls = []

    async def fake_execute(name, arguments):
        calls.append(name)
        if name == "tv_get_state":
            return SimpleNamespace(success=True, data={"data": dict(state)}, error=None)
        if name == "tv_set_timeframe":
            state["timeframe"] = arguments["timeframe"]
            return SimpleNamespace(success=True, data={"timeframe": state["timeframe"]}, error=None)
        if name == "tv_clear_drawings":
            return SimpleNamespace(success=True, data={"cleared": True}, error=None)
        if name == "tv_draw_horizontal_line":
            return SimpleNamespace(success=True, data={"drawing_id": f"line-{arguments['price']}"}, error=None)
        if name == "tv_capture_screenshot":
            return SimpleNamespace(
                success=True,
                data={"data": {"screenshot_url": "http://localhost/screenshot.png"}, "screenshot_url": "http://localhost/screenshot.png"},
                error=None,
            )
        if name == "get_price":
            return SimpleNamespace(success=True, data={"success": True, "symbol": "BTC", "price": 65000}, error=None)
        if name == "search_news_by_symbols":
            return SimpleNamespace(success=True, data={"success": True, "results": {"BTC": []}}, error=None)
        raise AssertionError(f"Unexpected tool call: {name}")

    monkeypatch.setattr(BaseAgent, "_route_intent", fake_route_intent)
    monkeypatch.setattr("agents.core.base.tool_registry.execute", fake_execute)

    agent = BaseAgent(name="TradingAgent", system_prompt="You are helpful.")

    response = asyncio.run(agent.process("Clear drawings and mark support at 65000 on BTC 4h", use_tools=True))

    assert response == "Pipeline response ok"
    assert [node.name for node in agent.last_pipeline_trace.pipeline_nodes] == [
        PIPELINE_NODE_CHART_ANALYSIS,
        PIPELINE_NODE_MARKET_SNAPSHOT,
        PIPELINE_NODE_RESPONSE_COMPOSER,
    ]
    assert agent.last_pipeline_trace.pipeline_nodes[0].metadata["chart_mode"] == "write"
    assert "tv_clear_drawings" in calls
    assert "tv_draw_horizontal_line" in calls
    assert "tv_capture_screenshot" in calls
    assert "tv_add_indicator" not in calls
    tool_names = {tool["name"] for tool in agent.client.messages.calls[0]["tools"]}
    assert tool_names == {"show_hint", "show_plan", "show_thinking_summary"}
    assert "Pipeline node instruction (chart_analysis):" in agent.client.messages.calls[0]["system"]


def test_base_agent_executes_portfolio_pipeline_nodes(monkeypatch):
    monkeypatch.setattr("agents.core.base.Anthropic", DummyAnthropic)
    monkeypatch.setattr("agents.core.base.AsyncAnthropic", DummyAsyncAnthropic)
    monkeypatch.setattr("agents.core.base.get_mem0_client", lambda: DummyMem0Client())
    register_trading_tools()

    async def fake_route_intent(self, user_input, history, market_context=None):
        return AgentIntentContext(
            intent="portfolio_review",
            confidence="high",
            preferred_tool_groups=["portfolio", "ui"],
        )

    async def fake_execute(name, arguments):
        return SimpleNamespace(success=True, data={"success": True, "tool": name}, error=None)

    monkeypatch.setattr(BaseAgent, "_route_intent", fake_route_intent)
    monkeypatch.setattr("agents.core.base.tool_registry.execute", fake_execute)

    agent = BaseAgent(name="TradingAgent", system_prompt="You are helpful.")
    response = asyncio.run(agent.process("Review my portfolio", use_tools=True))

    assert response == "Pipeline response ok"
    assert [node.name for node in agent.last_pipeline_trace.pipeline_nodes] == [
        PIPELINE_NODE_PORTFOLIO_SNAPSHOT,
        PIPELINE_NODE_RESPONSE_COMPOSER,
    ]
    assert agent.last_pipeline_trace.pipeline_nodes[0].status == "completed"
    assert agent.last_pipeline_trace.pipeline_nodes[1].status == "completed"
    assert agent.last_pipeline_trace.next_agent_status == "represented_by_pipeline_nodes"
    assert "Pipeline node instruction (portfolio_snapshot):" in agent.client.messages.calls[0]["system"]
    assert "Internal response-composer node observations:" in agent.client.messages.calls[0]["system"]


def test_base_agent_executes_execution_pipeline_nodes(monkeypatch):
    monkeypatch.setattr("agents.core.base.Anthropic", DummyAnthropic)
    monkeypatch.setattr("agents.core.base.AsyncAnthropic", DummyAsyncAnthropic)
    monkeypatch.setattr("agents.core.base.get_mem0_client", lambda: DummyMem0Client())
    register_trading_tools()

    async def fake_route_intent(self, user_input, history, market_context=None):
        return AgentIntentContext(
            intent="broker_execution",
            confidence="high",
            preferred_tool_groups=["execution", "portfolio", "ui"],
        )

    async def fake_execute(name, arguments):
        return SimpleNamespace(success=True, data={"success": True, "tool": name}, error=None)

    monkeypatch.setattr(BaseAgent, "_route_intent", fake_route_intent)
    monkeypatch.setattr("agents.core.base.tool_registry.execute", fake_execute)

    agent = BaseAgent(name="TradingAgent", system_prompt="You are helpful.")
    response = asyncio.run(
        agent.process(
            "Check execution readiness",
            use_tools=True,
            backpack_execution={"enabled": True, "exchange": "backpack"},
            drift_execution={"enabled": False, "exchange": "drift"},
        )
    )

    assert response == "Pipeline response ok"
    assert [node.name for node in agent.last_pipeline_trace.pipeline_nodes] == [
        PIPELINE_NODE_EXECUTION_SNAPSHOT,
        PIPELINE_NODE_RESPONSE_COMPOSER,
    ]
    assert agent.last_pipeline_trace.next_agent_status == "represented_by_pipeline_nodes"
    assert "Pipeline node instruction (execution_snapshot):" in agent.client.messages.calls[0]["system"]


def test_base_agent_executes_memory_pipeline_nodes(monkeypatch):
    monkeypatch.setattr("agents.core.base.Anthropic", DummyAnthropic)
    monkeypatch.setattr("agents.core.base.AsyncAnthropic", DummyAsyncAnthropic)
    monkeypatch.setattr("agents.core.base.get_mem0_client", lambda: DummyMem0Client())
    register_trading_tools()

    async def fake_route_intent(self, user_input, history, market_context=None):
        return AgentIntentContext(
            intent="memory_lookup",
            confidence="high",
            preferred_tool_groups=["memory", "ui"],
        )

    async def fake_execute(name, arguments):
        return SimpleNamespace(success=True, data={"success": True, "results": [{"memory": "User prefers SOL"}]}, error=None)

    monkeypatch.setattr(BaseAgent, "_route_intent", fake_route_intent)
    monkeypatch.setattr("agents.core.base.tool_registry.execute", fake_execute)

    agent = BaseAgent(name="TradingAgent", system_prompt="You are helpful.")
    response = asyncio.run(agent.process("What do you remember about me?", use_tools=True))

    assert response == "Pipeline response ok"
    assert [node.name for node in agent.last_pipeline_trace.pipeline_nodes] == [
        PIPELINE_NODE_MEMORY_SNAPSHOT,
        PIPELINE_NODE_RESPONSE_COMPOSER,
    ]
    assert agent.last_pipeline_trace.next_agent_status == "represented_by_pipeline_nodes"
    assert "Pipeline node instruction (memory_snapshot):" in agent.client.messages.calls[0]["system"]


def test_base_agent_executes_clarification_pipeline_nodes(monkeypatch):
    monkeypatch.setattr("agents.core.base.Anthropic", DummyAnthropic)
    monkeypatch.setattr("agents.core.base.AsyncAnthropic", DummyAsyncAnthropic)
    monkeypatch.setattr("agents.core.base.get_mem0_client", lambda: DummyMem0Client())
    register_trading_tools()

    async def fake_route_intent(self, user_input, history, market_context=None):
        return AgentIntentContext(
            intent="trade_setup",
            confidence="high",
            should_clarify=True,
            preferred_tool_groups=["chart", "ui"],
            clarification_reason="Asset is ambiguous.",
            suggested_hint_title="Which asset?",
            suggested_hint_options=[{"id": "btc", "text": "BTC"}, {"id": "sol", "text": "SOL"}],
        )

    monkeypatch.setattr(BaseAgent, "_route_intent", fake_route_intent)

    agent = BaseAgent(name="TradingAgent", system_prompt="You are helpful.")
    response = asyncio.run(agent.process("Check setup", use_tools=True))

    assert response == "Pipeline response ok"
    assert [node.name for node in agent.last_pipeline_trace.pipeline_nodes] == [
        PIPELINE_NODE_CLARIFICATION_PREP,
        PIPELINE_NODE_RESPONSE_COMPOSER,
    ]
    assert agent.last_pipeline_trace.next_agent_status == "clarification_node_completed"
    assert "Pipeline node instruction (clarification_prep):" in agent.client.messages.calls[0]["system"]
    tool_names = {tool["name"] for tool in agent.client.messages.calls[0]["tools"]}
    assert tool_names == {"show_hint"}


def test_base_agent_executes_general_fallback_pipeline_nodes(monkeypatch):
    monkeypatch.setattr("agents.core.base.Anthropic", DummyAnthropic)
    monkeypatch.setattr("agents.core.base.AsyncAnthropic", DummyAsyncAnthropic)
    monkeypatch.setattr("agents.core.base.get_mem0_client", lambda: DummyMem0Client())
    register_trading_tools()

    async def fake_route_intent(self, user_input, history, market_context=None):
        return AgentIntentContext(
            intent="market_analysis",
            confidence="low",
            preferred_tool_groups=["market", "chart", "ui"],
            routing_reason="Low confidence route",
        )

    monkeypatch.setattr(BaseAgent, "_route_intent", fake_route_intent)

    agent = BaseAgent(name="TradingAgent", system_prompt="You are helpful.")
    response = asyncio.run(agent.process("Analyze maybe this setup", use_tools=True))

    assert response == "Pipeline response ok"
    assert [node.name for node in agent.last_pipeline_trace.pipeline_nodes] == [
        PIPELINE_NODE_GENERAL_FALLBACK,
        PIPELINE_NODE_RESPONSE_COMPOSER,
    ]
    assert agent.last_pipeline_trace.next_agent_status == "general_node_completed"
    assert "Pipeline node instruction (general_fallback):" in agent.client.messages.calls[0]["system"]
    tool_names = {tool["name"] for tool in agent.client.messages.calls[0]["tools"]}
    assert tool_names == {"show_hint", "show_plan", "show_thinking_summary"}


def test_base_agent_low_confidence_chart_request_does_not_plan_chart_node(monkeypatch):
    monkeypatch.setattr("agents.core.base.Anthropic", DummyAnthropic)
    monkeypatch.setattr("agents.core.base.AsyncAnthropic", DummyAsyncAnthropic)
    monkeypatch.setattr("agents.core.base.get_mem0_client", lambda: DummyMem0Client())
    register_trading_tools()

    async def fake_route_intent(self, user_input, history, market_context=None):
        return AgentIntentContext(
            intent="market_analysis",
            confidence="low",
            preferred_tool_groups=["market", "chart", "ui"],
            indicator_preference="indicator_light",
            routing_reason="Low confidence route",
        )

    monkeypatch.setattr(BaseAgent, "_route_intent", fake_route_intent)

    agent = BaseAgent(name="TradingAgent", system_prompt="You are helpful.")
    response = asyncio.run(agent.process("Analyze the BTC chart with RSI", use_tools=True))

    assert response == "Pipeline response ok"
    assert [node.name for node in agent.last_pipeline_trace.pipeline_nodes] == [
        PIPELINE_NODE_GENERAL_FALLBACK,
        PIPELINE_NODE_RESPONSE_COMPOSER,
    ]
    tool_names = {tool["name"] for tool in agent.client.messages.calls[0]["tools"]}
    assert tool_names == {"show_hint", "show_plan", "show_thinking_summary"}
    assert "Pipeline node instruction (chart_analysis):" not in agent.client.messages.calls[0]["system"]
