import pytest

from agents.core.graph_executor import AgentNodeExecutionContext
from agents.core.pipeline import AgentPipelineNodePlan
from agents.intent_router import AgentIntentContext
from agents.nodes.response_composer import run_response_composer_node


@pytest.mark.asyncio
async def test_response_composer_node_summarizes_prior_observations():
    context = AgentNodeExecutionContext(
        agent=object(),
        user_input="Analyze BTC",
        messages=[],
        system_prompt="base prompt",
        intent_context=AgentIntentContext(intent="market_analysis", confidence="high"),
        market_context={},
        observations={
            "_node_instructions": {"chart_analysis": "Inspect chart"},
            "chart_analysis": {"status": "completed", "effective_symbol": "BTC"},
            "market_snapshot": {"status": "degraded", "resolved_symbol": "BTC"},
        },
    )
    plan = AgentPipelineNodePlan(name="response_composer")

    result = await run_response_composer_node(context, plan)

    assert result.status == "completed"
    assert result.metadata["observed_nodes"] == ["chart_analysis", "market_snapshot"]
    assert result.metadata["degraded_nodes"] == ["market_snapshot"]
    assert result.metadata["node_count"] == 2
    assert "Internal response-composer node observations:" in result.system_prompt_addition
