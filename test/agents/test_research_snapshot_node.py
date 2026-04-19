from types import SimpleNamespace

import pytest

from agents.core.graph_executor import AgentNodeExecutionContext
from agents.core.pipeline import AgentPipelineNodePlan
from agents.intent_router import AgentIntentContext
from agents.nodes.research_snapshot import run_research_snapshot_node


@pytest.mark.asyncio
async def test_research_snapshot_prefers_symbol_news_then_web_search():
    calls = []

    async def fake_tool(name, arguments):
        calls.append((name, arguments))
        if name == "search_news_by_symbols":
            return SimpleNamespace(
                success=True,
                data={
                    "success": True,
                    "results": {
                        "BTC": [
                            {
                                "title": "Bitcoin reacts to ETF flows",
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
        if name == "web_search":
            return SimpleNamespace(
                success=True,
                data={
                    "success": True,
                    "results": [
                        {
                            "title": "ETF flow context",
                            "url": "https://example.com/etf",
                            "snippet": "Broader BTC ETF context",
                        }
                    ],
                },
                error=None,
            )
        raise AssertionError(f"Unexpected tool call: {name}")

    context = AgentNodeExecutionContext(
        agent=object(),
        user_input="What is the latest BTC news impact?",
        messages=[],
        system_prompt="base prompt",
        intent_context=AgentIntentContext(intent="news_impact", confidence="high"),
        market_context={"scope_mode": "global"},
        call_tool=fake_tool,
    )
    plan = AgentPipelineNodePlan(name="research_snapshot", config={"max_headlines": 3, "max_search_results": 3})

    result = await run_research_snapshot_node(context, plan)

    assert result.status == "completed"
    assert result.metadata["resolved_symbol"] == "BTC"
    assert result.metadata["news_headlines"][0]["title"] == "Bitcoin reacts to ETF flows"
    assert result.metadata["web_results"][0]["title"] == "ETF flow context"
    assert calls[0][0] == "search_news_by_symbols"
    assert calls[1][0] == "web_search"


@pytest.mark.asyncio
async def test_research_snapshot_uses_trending_news_without_symbol():
    calls = []

    async def fake_tool(name, arguments):
        calls.append((name, arguments))
        if name == "get_trending_news":
            return SimpleNamespace(
                success=True,
                data={
                    "success": True,
                    "results": [
                        {
                            "title": "Macro liquidity shifts",
                            "source": "MockMacro",
                            "date": "2026-04-19T01:00:00+00:00",
                            "detected_at": "2026-04-19T01:05:00+00:00",
                            "is_new": True,
                        }
                    ],
                },
                error=None,
            )
        if name == "web_search":
            return SimpleNamespace(
                success=True,
                data={"success": True, "results": []},
                error=None,
            )
        raise AssertionError(f"Unexpected tool call: {name}")

    context = AgentNodeExecutionContext(
        agent=object(),
        user_input="What is the macro context today?",
        messages=[],
        system_prompt="base prompt",
        intent_context=AgentIntentContext(intent="macro_context", confidence="high"),
        market_context={"scope_mode": "global"},
        call_tool=fake_tool,
    )
    plan = AgentPipelineNodePlan(name="research_snapshot", config={"max_headlines": 3, "max_search_results": 3})

    result = await run_research_snapshot_node(context, plan)

    assert result.status == "completed"
    assert result.metadata["resolved_symbol"] is None
    assert result.metadata["news_headlines"][0]["title"] == "Macro liquidity shifts"
    assert calls[0][0] == "get_trending_news"
    assert calls[1][0] == "web_search"
