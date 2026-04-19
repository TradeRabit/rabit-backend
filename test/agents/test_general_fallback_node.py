import pytest

from agents.core.graph_executor import AgentNodeExecutionContext
from agents.core.pipeline import AgentPipelineNodePlan
from agents.intent_router import AgentIntentContext
from agents.nodes.general_fallback import run_general_fallback_node


@pytest.mark.asyncio
async def test_general_fallback_node_builds_low_confidence_context():
    context = AgentNodeExecutionContext(
        agent=object(),
        user_input="Maybe analyze this setup",
        messages=[],
        system_prompt="base prompt",
        intent_context=AgentIntentContext(
            intent="market_analysis",
            confidence="low",
            routing_reason="Low confidence route",
            goal_summary="Analyze the market carefully",
        ),
        market_context={},
    )
    plan = AgentPipelineNodePlan(name="general_fallback")

    result = await run_general_fallback_node(context, plan)

    assert result.status == "completed"
    assert result.metadata["routing_intent"] == "market_analysis"
    assert result.metadata["confidence"] == "low"
    assert result.metadata["routing_reason"] == "Low confidence route"
    assert result.metadata["goal_summary"] == "Analyze the market carefully"
    assert "Internal general-fallback node observations:" in result.system_prompt_addition
