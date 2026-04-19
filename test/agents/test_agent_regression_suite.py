import pytest

from agents.core.pipeline import resolve_selected_next_agent
from agents.intent_router import parse_intent_response


@pytest.mark.parametrize(
    ("raw_json", "expected_intent", "expected_specialist", "expected_groups"),
    [
        (
            """
            {
              "intent": "market_analysis",
              "user_goal_type": "analyze",
              "goal_summary": "Analyze BTC structure",
              "analysis_mode": "technical",
              "analysis_scope": "full_setup",
              "indicator_preference": "indicator_light",
              "need_indicator_confirmation": false,
              "inferred_indicator_hint": "trend indicators",
              "confidence": "high",
              "preferred_tool_groups": ["market", "chart", "ui"],
              "routing_reason": "Market analysis request",
              "response_language": "english",
              "should_clarify": false,
              "clarification_reason": "",
              "suggested_hint_title": "",
              "suggested_hint_options": []
            }
            """,
            "market_analysis",
            "market_specialist",
            {"market", "chart", "ui"},
        ),
        (
            """
            {
              "intent": "broker_execution",
              "user_goal_type": "execution_prep",
              "goal_summary": "Check order readiness",
              "analysis_mode": "operational",
              "analysis_scope": "risk_review",
              "indicator_preference": "auto",
              "need_indicator_confirmation": false,
              "inferred_indicator_hint": "",
              "confidence": "high",
              "preferred_tool_groups": ["execution", "portfolio", "ui"],
              "routing_reason": "Execution request",
              "response_language": "english",
              "should_clarify": false,
              "clarification_reason": "",
              "suggested_hint_title": "",
              "suggested_hint_options": []
            }
            """,
            "broker_execution",
            "execution_specialist",
            {"execution", "portfolio", "ui"},
        ),
        (
            """
            {
              "intent": "journal_debrief",
              "user_goal_type": "reflect",
              "goal_summary": "Review yesterday trade",
              "analysis_mode": "memory",
              "analysis_scope": "debrief",
              "indicator_preference": "auto",
              "need_indicator_confirmation": false,
              "inferred_indicator_hint": "",
              "confidence": "high",
              "preferred_tool_groups": ["memory", "ui"],
              "routing_reason": "Debrief request",
              "response_language": "english",
              "should_clarify": false,
              "clarification_reason": "",
              "suggested_hint_title": "",
              "suggested_hint_options": []
            }
            """,
            "journal_debrief",
            "memory_specialist",
            {"memory", "ui"},
        ),
        (
            """
            {
              "intent": "education",
              "user_goal_type": "learn_path",
              "goal_summary": "What should I learn next",
              "analysis_mode": "general",
              "analysis_scope": "general",
              "indicator_preference": "auto",
              "need_indicator_confirmation": false,
              "inferred_indicator_hint": "",
              "confidence": "high",
              "preferred_tool_groups": ["research", "ui"],
              "routing_reason": "Learning request",
              "response_language": "english",
              "should_clarify": false,
              "clarification_reason": "",
              "suggested_hint_title": "",
              "suggested_hint_options": []
            }
            """,
            "education",
            "research_specialist",
            {"research", "ui"},
        ),
    ],
)
def test_agent_regression_suite(raw_json, expected_intent, expected_specialist, expected_groups):
    context = parse_intent_response(raw_json)

    assert context.intent == expected_intent
    assert resolve_selected_next_agent(context, context.goal_summary) == expected_specialist
    assert set(context.preferred_tool_groups) == expected_groups
    assert context.should_clarify is False
