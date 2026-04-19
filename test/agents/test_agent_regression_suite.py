import pytest

from agents.pipeline.pipeline import (
    PIPELINE_NODE_EXECUTION_SNAPSHOT,
    PIPELINE_NODE_GENERAL_FALLBACK,
    PIPELINE_NODE_MEMORY_SNAPSHOT,
    PIPELINE_NODE_PORTFOLIO_SNAPSHOT,
    PIPELINE_NODE_RESEARCH_SNAPSHOT,
    PIPELINE_NODE_RESPONSE_COMPOSER,
    build_pipeline_nodes,
    resolve_selected_next_agent,
    should_enable_chart_write,
)
from agents.pipeline.intent_router import parse_intent_response


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


@pytest.mark.parametrize(
    ("request_text", "expected_write"),
    [
        ("Analyze the BTC chart with RSI and MACD", False),
        ("Can you maybe mark something on the chart?", False),
        ("Clear drawings and mark support at 65000 on BTC 4h", True),
        ("Draw a trend line from 2026-04-10 64000 to 2026-04-12 66000 on BTC", True),
    ],
)
def test_chart_write_ambiguity_matrix(request_text, expected_write):
    context = parse_intent_response(
        """
        {
          "intent": "trade_setup",
          "user_goal_type": "setup_refinement",
          "goal_summary": "Work with the chart",
          "analysis_mode": "technical",
          "analysis_scope": "full_setup",
          "indicator_preference": "auto",
          "need_indicator_confirmation": false,
          "inferred_indicator_hint": "",
          "confidence": "high",
          "preferred_tool_groups": ["market", "chart", "ui"],
          "routing_reason": "Chart-oriented request",
          "response_language": "english",
          "should_clarify": false,
          "clarification_reason": "",
          "suggested_hint_title": "",
          "suggested_hint_options": []
        }
        """
    )
    assert should_enable_chart_write(context, request_text) is expected_write


@pytest.mark.parametrize(
    ("confidence", "should_clarify", "expected_nodes"),
    [
        ("high", False, [PIPELINE_NODE_PORTFOLIO_SNAPSHOT, PIPELINE_NODE_RESPONSE_COMPOSER]),
        ("low", False, [PIPELINE_NODE_GENERAL_FALLBACK, PIPELINE_NODE_RESPONSE_COMPOSER]),
    ],
)
def test_portfolio_ambiguity_matrix(confidence, should_clarify, expected_nodes):
    nodes = build_pipeline_nodes(
        intent_context=parse_intent_response(
            f"""
            {{
              "intent": "portfolio_review",
              "user_goal_type": "review",
              "goal_summary": "Review my portfolio",
              "analysis_mode": "portfolio",
              "analysis_scope": "overview",
              "indicator_preference": "auto",
              "need_indicator_confirmation": false,
              "inferred_indicator_hint": "",
              "confidence": "{confidence}",
              "preferred_tool_groups": ["portfolio", "ui"],
              "routing_reason": "Portfolio request",
              "response_language": "english",
              "should_clarify": {str(should_clarify).lower()},
              "clarification_reason": "",
              "suggested_hint_title": "",
              "suggested_hint_options": []
            }}
            """
        ),
        user_input="Review my portfolio",
    )
    assert [node.name for node in nodes] == expected_nodes


@pytest.mark.parametrize(
    ("user_input", "expected_nodes"),
    [
        ("What recent SOL news matters right now?", ["market_snapshot", PIPELINE_NODE_RESEARCH_SNAPSHOT, PIPELINE_NODE_RESPONSE_COMPOSER]),
        ("What recent BTC news matters right now?", ["market_snapshot", PIPELINE_NODE_RESEARCH_SNAPSHOT, PIPELINE_NODE_RESPONSE_COMPOSER]),
        ("What macro news matters right now?", [PIPELINE_NODE_RESEARCH_SNAPSHOT, PIPELINE_NODE_RESPONSE_COMPOSER]),
    ],
)
def test_research_ambiguity_matrix(user_input, expected_nodes):
    context = parse_intent_response(
        """
        {
          "intent": "news_impact",
          "user_goal_type": "analyze",
          "goal_summary": "Review catalyst impact",
          "analysis_mode": "research",
          "analysis_scope": "macro",
          "indicator_preference": "auto",
          "need_indicator_confirmation": false,
          "inferred_indicator_hint": "",
          "confidence": "high",
          "preferred_tool_groups": ["research", "ui"],
          "routing_reason": "News request",
          "response_language": "english",
          "should_clarify": false,
          "clarification_reason": "",
          "suggested_hint_title": "",
          "suggested_hint_options": []
        }
        """
    )
    nodes = build_pipeline_nodes(intent_context=context, user_input=user_input)
    assert [node.name for node in nodes] == expected_nodes


@pytest.mark.parametrize(
    ("confidence", "expected_nodes"),
    [
        ("high", [PIPELINE_NODE_MEMORY_SNAPSHOT, PIPELINE_NODE_RESPONSE_COMPOSER]),
        ("low", [PIPELINE_NODE_GENERAL_FALLBACK, PIPELINE_NODE_RESPONSE_COMPOSER]),
    ],
)
def test_memory_ambiguity_matrix(confidence, expected_nodes):
    nodes = build_pipeline_nodes(
        intent_context=parse_intent_response(
            f"""
            {{
              "intent": "memory_lookup",
              "user_goal_type": "recall",
              "goal_summary": "Recall what I said before",
              "analysis_mode": "memory",
              "analysis_scope": "recall",
              "indicator_preference": "auto",
              "need_indicator_confirmation": false,
              "inferred_indicator_hint": "",
              "confidence": "{confidence}",
              "preferred_tool_groups": ["memory", "ui"],
              "routing_reason": "Memory request",
              "response_language": "english",
              "should_clarify": false,
              "clarification_reason": "",
              "suggested_hint_title": "",
              "suggested_hint_options": []
            }}
            """
        ),
        user_input="What did I say about my SOL strategy?",
    )
    assert [node.name for node in nodes] == expected_nodes


@pytest.mark.parametrize(
    ("confidence", "expected_nodes"),
    [
        ("high", [PIPELINE_NODE_EXECUTION_SNAPSHOT, PIPELINE_NODE_RESPONSE_COMPOSER]),
        ("low", [PIPELINE_NODE_GENERAL_FALLBACK, PIPELINE_NODE_RESPONSE_COMPOSER]),
    ],
)
def test_execution_degraded_matrix(confidence, expected_nodes):
    nodes = build_pipeline_nodes(
        intent_context=parse_intent_response(
            f"""
            {{
              "intent": "broker_execution",
              "user_goal_type": "execution_prep",
              "goal_summary": "Check order readiness",
              "analysis_mode": "operational",
              "analysis_scope": "readiness",
              "indicator_preference": "auto",
              "need_indicator_confirmation": false,
              "inferred_indicator_hint": "",
              "confidence": "{confidence}",
              "preferred_tool_groups": ["execution", "portfolio", "ui"],
              "routing_reason": "Execution request",
              "response_language": "english",
              "should_clarify": false,
              "clarification_reason": "",
              "suggested_hint_title": "",
              "suggested_hint_options": []
            }}
            """
        ),
        user_input="Can I execute this trade now?",
    )
    assert [node.name for node in nodes] == expected_nodes
