import asyncio

from agents.core.graph_executor import AgentNodeExecutionContext
from agents.pipeline.intent_router import AgentIntentContext
from agents.pipeline.pipeline import AgentPipelineNodePlan
from agents.nodes.risk_review import run_risk_review_node


def test_risk_review_node_flags_missing_invalidation_and_fresh_news():
    context = AgentNodeExecutionContext(
        agent=None,
        user_input="Review BTC risk and setup quality",
        messages=[],
        system_prompt="You are helpful.",
        intent_context=AgentIntentContext(
            intent="market_analysis",
            confidence="high",
            user_goal_type="risk_review",
            analysis_scope="risk_review",
        ),
        market_context={"symbol": "BTC", "timeframe": "4H"},
        observations={
            "chart_analysis": {
                "status": "completed",
                "effective_symbol": "BTC",
                "effective_timeframe": "240",
                "indicator_values": {"RSI": 74.2},
                "applied_actions": [],
                "requested_actions": [],
            },
            "market_snapshot": {
                "status": "completed",
                "resolved_symbol": "BTC",
                "news_headlines": [
                    {"title": "Fresh BTC catalyst", "is_new": True},
                ],
            },
        },
    )
    plan = AgentPipelineNodePlan(name="risk_review")

    result = asyncio.run(run_risk_review_node(context, plan))

    assert result.status == "completed"
    assert result.metadata["resolved_symbol"] == "BTC"
    assert result.metadata["caution_level"] in {"medium", "high"}
    assert result.metadata["invalidation_quality"] == "missing"
    assert result.metadata["news_fragility"] == "elevated"
    assert result.metadata["confluence_strength"] in {"medium", "high"}
    flags = {item["flag"] for item in result.metadata["risk_flags"]}
    assert "no_explicit_invalidation_observed" in flags
    assert "fresh_news_present" in flags
    assert "rsi_overbought" in flags
    assert "Internal risk-review node observations:" in result.system_prompt_addition


def test_risk_review_node_recognizes_explicit_invalidation_marker():
    context = AgentNodeExecutionContext(
        agent=None,
        user_input="Mark invalidation at 64000 and review the setup",
        messages=[],
        system_prompt="You are helpful.",
        intent_context=AgentIntentContext(
            intent="trade_setup",
            confidence="high",
            user_goal_type="risk_review",
            analysis_scope="risk_review",
        ),
        market_context={"symbol": "BTC"},
        observations={
            "chart_analysis": {
                "status": "completed",
                "effective_symbol": "BTC",
                "applied_actions": [{"action": "draw_horizontal_line", "text": "Invalidation"}],
                "requested_actions": [{"action": "draw_horizontal_line", "text": "Invalidation"}],
            }
        },
    )
    plan = AgentPipelineNodePlan(name="risk_review")

    result = asyncio.run(run_risk_review_node(context, plan))

    assert result.status == "completed"
    assert result.metadata["explicit_invalidation_present"] is True
    assert result.metadata["invalidation_quality"] == "explicit"
    assert result.metadata["risk_summary"]["invalidation_quality"] == "explicit"
    assert result.metadata["risk_summary"]["caution_level"] == result.metadata["caution_level"]
    flags = {item["flag"] for item in result.metadata["risk_flags"]}
    assert "no_explicit_invalidation_observed" not in flags


def test_risk_review_node_marks_execution_disabled_and_low_confluence():
    context = AgentNodeExecutionContext(
        agent=None,
        user_input="Check if this setup is worth taking",
        messages=[],
        system_prompt="You are helpful.",
        intent_context=AgentIntentContext(
            intent="broker_execution",
            confidence="high",
            user_goal_type="risk_review",
            analysis_scope="risk_review",
        ),
        market_context={"symbol": "SOL"},
        observations={
            "execution_snapshot": {
                "status": "completed",
                "execution_sections": {
                    "backpack_execution": {"enabled": False},
                    "drift_execution": {"enabled": False},
                },
            },
        },
    )
    plan = AgentPipelineNodePlan(name="risk_review")

    result = asyncio.run(run_risk_review_node(context, plan))

    assert result.status == "completed"
    assert result.metadata["execution_readiness"] == "disabled"
    assert result.metadata["confluence_strength"] == "low"
    flags = {item["flag"] for item in result.metadata["risk_flags"]}
    assert "execution_not_enabled" in flags
