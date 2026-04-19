import asyncio
from types import SimpleNamespace

from agents.core.graph_executor import AgentNodeExecutionContext
from agents.pipeline.pipeline import AgentPipelineNodePlan
from agents.pipeline.intent_router import AgentIntentContext
from agents.nodes.chart_analysis import run_chart_analysis_node


def _success(data):
    return SimpleNamespace(success=True, data=data, error=None)


def test_chart_analysis_blocks_symbol_change_for_locked_asset():
    state = {
        "symbol": "BTC",
        "timeframe": "60",
        "indicators": [],
    }
    calls = []

    async def call_tool(name, arguments):
        calls.append((name, arguments))
        if name == "tv_get_state":
            return _success({"data": dict(state)})
        if name == "tv_add_indicator":
            state["indicators"].append(
                {"name": arguments["indicator"], "entity_id": "ind-rsi"}
            )
            return _success({"entity_id": "ind-rsi"})
        if name == "tv_get_quote":
            return _success({"data": {"symbol": state["symbol"], "price": 65000}})
        if name == "tv_get_indicator_values":
            return _success({"data": {"RSI": 58.1}})
        raise AssertionError(f"Unexpected tool call: {name}")

    context = AgentNodeExecutionContext(
        agent=object(),
        user_input="Analyze the ETH chart with RSI",
        messages=[],
        system_prompt="base prompt",
        intent_context=AgentIntentContext(
            intent="market_analysis",
            confidence="high",
            preferred_tool_groups=["market", "chart", "ui"],
            indicator_preference="indicator_light",
        ),
        market_context={"scope_mode": "locked_asset", "symbol": "BTC", "timeframe": "60"},
        call_tool=call_tool,
    )
    plan = AgentPipelineNodePlan(name="chart_analysis", config={"allow_symbol_change_when_global": True})

    result = asyncio.run(run_chart_analysis_node(context, plan))

    assert result.status == "completed"
    assert result.metadata["symbol_change_blocked"] is True
    assert result.metadata["effective_symbol"] == "BTC"
    assert result.metadata["requested_symbol"] == "ETH"
    assert "tv_set_symbol" not in [name for name, _ in calls]
    assert [name for name, _ in calls].count("tv_add_indicator") == 1


def test_chart_analysis_global_scope_can_change_symbol_and_add_indicators():
    state = {
        "symbol": "BTC",
        "timeframe": "60",
        "indicators": [],
    }
    calls = []
    entity_counter = {"count": 0}

    async def call_tool(name, arguments):
        calls.append((name, arguments))
        if name == "tv_get_state":
            return _success({"data": dict(state)})
        if name == "tv_set_symbol":
            state["symbol"] = arguments["symbol"]
            return _success({"symbol": state["symbol"]})
        if name == "tv_set_timeframe":
            state["timeframe"] = arguments["timeframe"]
            return _success({"timeframe": state["timeframe"]})
        if name == "tv_add_indicator":
            entity_counter["count"] += 1
            entity_id = f"ind-{entity_counter['count']}"
            state["indicators"].append(
                {"name": arguments["indicator"], "entity_id": entity_id}
            )
            return _success({"entity_id": entity_id})
        if name == "tv_get_quote":
            return _success({"data": {"symbol": state["symbol"], "price": 178.4}})
        if name == "tv_get_indicator_values":
            return _success({"data": {"RSI": 54.2, "MACD": {"line": 1.1, "signal": 0.8}}})
        raise AssertionError(f"Unexpected tool call: {name}")

    context = AgentNodeExecutionContext(
        agent=object(),
        user_input="Analyze the SOL chart on 4h with RSI and MACD",
        messages=[],
        system_prompt="base prompt",
        intent_context=AgentIntentContext(
            intent="market_analysis",
            confidence="high",
            analysis_mode="technical",
            preferred_tool_groups=["market", "chart", "ui"],
            indicator_preference="indicator_heavy",
            inferred_indicator_hint="RSI and MACD",
        ),
        market_context={"scope_mode": "global", "symbol": "BTC", "timeframe": "60"},
        call_tool=call_tool,
    )
    plan = AgentPipelineNodePlan(
        name="chart_analysis",
        config={
            "allow_symbol_change_when_global": True,
            "allow_indicator_add": True,
            "allow_chart_write": False,
            "max_steps": 4,
        },
    )

    result = asyncio.run(run_chart_analysis_node(context, plan))

    tool_names = [name for name, _ in calls]
    assert result.status == "completed"
    assert result.metadata["effective_symbol"] == "SOL"
    assert result.metadata["effective_timeframe"] == "240"
    assert len(result.metadata["added_indicators"]) == 2
    assert "tv_set_symbol" in tool_names
    assert "tv_set_timeframe" in tool_names
    assert tool_names.count("tv_add_indicator") == 2
    assert "tv_draw_line" not in tool_names
    assert "tv_create_alert" not in tool_names
    assert "Internal chart-analysis node observations" in result.system_prompt_addition


def test_chart_write_mode_draws_levels_and_captures_screenshot():
    state = {
        "symbol": "BTC",
        "timeframe": "60",
        "indicators": [],
    }
    calls = []
    persisted_artifacts = []

    async def call_tool(name, arguments):
        calls.append((name, arguments))
        if name == "tv_get_state":
            return _success({"data": dict(state)})
        if name == "tv_set_symbol":
            state["symbol"] = arguments["symbol"]
            return _success({"symbol": state["symbol"]})
        if name == "tv_set_timeframe":
            state["timeframe"] = arguments["timeframe"]
            return _success({"timeframe": state["timeframe"]})
        if name == "tv_clear_drawings":
            return _success({"cleared": True})
        if name == "tv_draw_horizontal_line":
            return _success({"drawing_id": f"line-{arguments['price']}"})
        if name == "tv_capture_screenshot":
            return _success({"data": {"screenshot_url": "http://localhost/screenshot.png"}})
        raise AssertionError(f"Unexpected tool call: {name}")

    def persist_artifact(**kwargs):
        artifact = {
            "artifact_id": "artifact-1",
            "scope_id": "scope-1",
            **kwargs,
        }
        persisted_artifacts.append(artifact)
        return artifact

    context = AgentNodeExecutionContext(
        agent=object(),
        user_input="Clear drawings and mark support at 65000 plus resistance at 68000 on ETH 4h",
        messages=[],
        system_prompt="base prompt",
        intent_context=AgentIntentContext(
            intent="trade_setup",
            confidence="high",
            preferred_tool_groups=["market", "chart", "ui"],
        ),
        market_context={"scope_mode": "global", "symbol": "BTC", "timeframe": "60"},
        call_tool=call_tool,
        persist_artifact=persist_artifact,
    )
    plan = AgentPipelineNodePlan(
        name="chart_analysis",
        config={
            "chart_mode": "write",
            "allow_symbol_change_when_global": True,
            "allow_chart_write": True,
            "capture_screenshot_after_write": True,
        },
    )

    result = asyncio.run(run_chart_analysis_node(context, plan))

    tool_names = [name for name, _ in calls]
    assert result.status == "completed"
    assert result.metadata["chart_mode"] == "write"
    assert result.metadata["effective_symbol"] == "ETH"
    assert result.metadata["effective_timeframe"] == "240"
    assert "tv_clear_drawings" in tool_names
    assert tool_names.count("tv_draw_horizontal_line") == 2
    assert "tv_capture_screenshot" in tool_names
    assert "tv_add_indicator" not in tool_names
    assert result.metadata["applied_actions"][0]["action"] == "clear_drawings"
    assert result.metadata["artifacts"][0]["artifact_id"] == "artifact-1"
    assert persisted_artifacts[0]["kind"] == "chart_write_screenshot"
    assert "Internal chart-write node observations" in result.system_prompt_addition


def test_chart_write_mode_blocks_symbol_change_for_locked_asset():
    state = {
        "symbol": "BTC",
        "timeframe": "60",
        "indicators": [],
    }
    calls = []

    async def call_tool(name, arguments):
        calls.append((name, arguments))
        if name == "tv_get_state":
            return _success({"data": dict(state)})
        if name == "tv_draw_horizontal_line":
            return _success({"drawing_id": "line-1"})
        if name == "tv_capture_screenshot":
            return _success({"data": {"screenshot_url": "http://localhost/screenshot.png"}})
        raise AssertionError(f"Unexpected tool call: {name}")

    context = AgentNodeExecutionContext(
        agent=object(),
        user_input="Mark support at 65000 on ETH",
        messages=[],
        system_prompt="base prompt",
        intent_context=AgentIntentContext(
            intent="trade_setup",
            confidence="high",
            preferred_tool_groups=["market", "chart", "ui"],
        ),
        market_context={"scope_mode": "locked_asset", "symbol": "BTC", "timeframe": "60"},
        call_tool=call_tool,
    )
    plan = AgentPipelineNodePlan(
        name="chart_analysis",
        config={
            "chart_mode": "write",
            "allow_symbol_change_when_global": True,
            "allow_chart_write": True,
            "capture_screenshot_after_write": True,
        },
    )

    result = asyncio.run(run_chart_analysis_node(context, plan))

    tool_names = [name for name, _ in calls]
    assert result.status == "completed"
    assert result.metadata["symbol_change_blocked"] is True
    assert result.metadata["effective_symbol"] == "BTC"
    assert "tv_set_symbol" not in tool_names
    assert "tv_draw_horizontal_line" in tool_names
