from types import SimpleNamespace

import pytest

from agents.core.graph_executor import AgentNodeExecutionContext
from agents.pipeline.pipeline import AgentPipelineNodePlan
from agents.pipeline.intent_router import AgentIntentContext
from agents.nodes.market_snapshot import run_market_snapshot_node


@pytest.mark.asyncio
async def test_market_snapshot_node_uses_chart_symbol_and_collects_price_and_news():
    calls = []

    async def fake_tool(name, arguments):
        calls.append((name, arguments))
        if name == "get_price":
            return SimpleNamespace(
                success=True,
                data={"success": True, "symbol": "BTC", "price": 65000, "change_24h": 1.2},
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
                                "title": "Bitcoin sees ETF inflows",
                                "source": "MockDesk",
                                "date": "2026-04-19T01:00:00+00:00",
                                "detected_at": "2026-04-19T01:05:00+00:00",
                                "is_new": True,
                            }
                        ]
                    },
                },
                error=None,
            )
        raise AssertionError(f"Unexpected tool call: {name}")

    context = AgentNodeExecutionContext(
        agent=object(),
        user_input="Analyze BTC",
        messages=[],
        system_prompt="base prompt",
        intent_context=AgentIntentContext(intent="market_analysis", confidence="high"),
        market_context={"scope_mode": "global"},
        call_tool=fake_tool,
        observations={"chart_analysis": {"effective_symbol": "BTC"}},
    )
    plan = AgentPipelineNodePlan(name="market_snapshot", config={"max_headlines": 3})

    result = await run_market_snapshot_node(context, plan)

    assert result.status == "completed"
    assert result.metadata["resolved_symbol"] == "BTC"
    assert result.metadata["price_snapshot"]["price"] == 65000
    assert result.metadata["news_headlines"][0]["title"] == "Bitcoin sees ETF inflows"
    assert "Internal market-snapshot node observations:" in result.system_prompt_addition
    assert calls[0][0] == "get_price"
    assert calls[1][0] == "search_news_by_symbols"


@pytest.mark.asyncio
async def test_market_snapshot_node_skips_without_symbol():
    async def fake_tool(name, arguments):
        raise AssertionError("No tools should be called when no symbol is available")

    context = AgentNodeExecutionContext(
        agent=object(),
        user_input="Give me a broad market view",
        messages=[],
        system_prompt="base prompt",
        intent_context=AgentIntentContext(intent="research", confidence="high"),
        market_context={"scope_mode": "global"},
        call_tool=fake_tool,
        observations={},
    )
    plan = AgentPipelineNodePlan(name="market_snapshot", config={"max_headlines": 3})

    result = await run_market_snapshot_node(context, plan)

    assert result.status == "skipped"
    assert result.metadata["resolved_symbol"] is None
