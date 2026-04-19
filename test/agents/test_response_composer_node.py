import pytest

from agents.core.graph_executor import AgentNodeExecutionContext
from agents.pipeline.pipeline import AgentPipelineNodePlan
from agents.pipeline.intent_router import AgentIntentContext
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
    assert result.metadata["primary_evidence_nodes"] == ["chart_analysis"]
    assert result.metadata["supporting_nodes"] == []
    assert result.metadata["recommended_posture"] == "cautious"
    assert result.metadata["conflict_flags"][0]["flag"] == "degraded_upstream_context"
    assert "Internal response-composer node observations:" in result.system_prompt_addition


@pytest.mark.asyncio
async def test_response_composer_node_detects_symbol_conflict_and_risk_posture():
    class DummyAgent:
        last_pipeline_artifacts = [{"artifact_id": "artifact-1"}]

    context = AgentNodeExecutionContext(
        agent=DummyAgent(),
        user_input="Review BTC setup",
        messages=[],
        system_prompt="base prompt",
        intent_context=AgentIntentContext(intent="trade_setup", confidence="high"),
        market_context={"symbol": "BTC", "timeframe": "4H"},
        observations={
            "chart_analysis": {
                "status": "completed",
                "effective_symbol": "BTC",
                "effective_timeframe": "240",
            },
            "market_snapshot": {
                "status": "completed",
                "resolved_symbol": "ETH",
            },
            "risk_review": {
                "status": "completed",
                "caution_level": "high",
                "fresh_headline_count": 1,
            },
        },
    )
    plan = AgentPipelineNodePlan(name="response_composer")

    result = await run_response_composer_node(context, plan)

    assert result.status == "completed"
    assert result.metadata["resolved_symbol"] == "BTC"
    assert result.metadata["resolved_timeframe"] == "240"
    assert result.metadata["artifact_count"] == 1
    assert result.metadata["primary_evidence_nodes"] == ["risk_review", "chart_analysis", "market_snapshot"]
    assert result.metadata["recommended_posture"] == "cautious"
    conflict_flags = {item["flag"] for item in result.metadata["conflict_flags"]}
    assert "symbol_context_mismatch" in conflict_flags
    assert "fresh_news_fragility" in conflict_flags
    assert "high_risk_posture" in conflict_flags
