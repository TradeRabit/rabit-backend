import asyncio
from types import SimpleNamespace

from agents.core.graph_executor import AgentNodeExecutionContext
from agents.core.pipeline import AgentPipelineNodePlan
from agents.intent_router import AgentIntentContext
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
