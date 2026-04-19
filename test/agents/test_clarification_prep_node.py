import pytest

from agents.core.graph_executor import AgentNodeExecutionContext
from agents.pipeline.pipeline import AgentPipelineNodePlan
from agents.pipeline.intent_router import AgentIntentContext
from agents.nodes.clarification_prep import run_clarification_prep_node


@pytest.mark.asyncio
async def test_clarification_prep_node_builds_structured_hint_context():
    context = AgentNodeExecutionContext(
        agent=object(),
        user_input="Check setup",
        messages=[],
        system_prompt="base prompt",
        intent_context=AgentIntentContext(
            intent="trade_setup",
            confidence="high",
            should_clarify=True,
            clarification_reason="Asset is ambiguous.",
            suggested_hint_title="Which asset?",
            suggested_hint_options=[{"id": "btc", "text": "BTC"}],
        ),
        market_context={},
    )
    plan = AgentPipelineNodePlan(name="clarification_prep")

    result = await run_clarification_prep_node(context, plan)

    assert result.status == "completed"
    assert result.metadata["should_clarify"] is True
    assert result.metadata["clarification_reason"] == "Asset is ambiguous."
    assert result.metadata["suggested_hint_title"] == "Which asset?"
    assert result.metadata["suggested_hint_options"] == [{"id": "btc", "text": "BTC"}]
    assert "Internal clarification-prep node observations:" in result.system_prompt_addition
