from types import SimpleNamespace

import pytest

from agents.core.graph_executor import AgentNodeExecutionContext
from agents.pipeline.pipeline import AgentPipelineNodePlan
from agents.pipeline.intent_router import AgentIntentContext
from agents.nodes.portfolio_snapshot import run_portfolio_snapshot_node


@pytest.mark.asyncio
async def test_portfolio_snapshot_collects_account_state():
    calls = []

    async def fake_tool(name, arguments):
        calls.append(name)
        return SimpleNamespace(success=True, data={"success": True, "tool": name}, error=None)

    context = AgentNodeExecutionContext(
        agent=object(),
        user_input="Review my portfolio",
        messages=[],
        system_prompt="base prompt",
        intent_context=AgentIntentContext(intent="portfolio_review", confidence="high"),
        market_context={},
        call_tool=fake_tool,
    )
    plan = AgentPipelineNodePlan(name="portfolio_snapshot", config={})

    result = await run_portfolio_snapshot_node(context, plan)

    assert result.status == "completed"
    assert "backpack_get_balances" in result.metadata["portfolio_sections"]
    assert "drift_get_positions" in result.metadata["portfolio_sections"]
    assert "Internal portfolio-snapshot node observations:" in result.system_prompt_addition
    assert "backpack_get_balances" in calls
    assert "drift_get_positions" in calls
