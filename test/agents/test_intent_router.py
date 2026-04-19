from agents.pipeline.intent_router import AgentIntentContext, build_intent_prompt, parse_intent_response
from agents.tools import ToolDefinition, ToolParameter, ToolRegistry


def test_parse_intent_response_builds_allowed_tool_names():
    context = parse_intent_response(
        """
        {
          "intent": "memory_lookup",
          "user_goal_type": "remember",
          "goal_summary": "Find saved user preferences",
          "analysis_mode": "memory",
          "analysis_scope": "comparison",
          "indicator_preference": "indicator_light",
          "need_indicator_confirmation": true,
          "inferred_indicator_hint": "memory recall only",
          "confidence": "high",
          "preferred_tool_groups": ["memory", "ui"],
          "routing_reason": "User is asking to recall saved information",
          "response_language": "match_user",
          "should_clarify": true,
          "clarification_reason": "Need to know which memory bucket the user means",
          "suggested_hint_title": "What memory do you want to review?",
          "suggested_hint_options": [
            {"id": "risk", "text": "Risk preferences"},
            {"id": "profile", "text": "Profile details"}
          ]
        }
        """
    )

    assert context.intent == "memory_lookup"
    assert context.user_goal_type == "remember"
    assert context.analysis_mode == "memory"
    assert context.analysis_scope == "comparison"
    assert context.indicator_preference == "indicator_light"
    assert context.need_indicator_confirmation is True
    assert context.inferred_indicator_hint == "memory recall only"
    assert "get_user_memory" in context.allowed_tool_names
    assert "show_hint" in context.allowed_tool_names
    assert "get_price" not in context.allowed_tool_names
    assert context.response_language == "match_user"
    assert context.should_clarify is True
    assert context.suggested_hint_options[0]["id"] == "risk"


def test_parse_intent_response_falls_back_on_invalid_payload():
    context = parse_intent_response("not-json")

    assert context.intent == "general_chat"
    assert context.user_goal_type == "ask"
    assert context.analysis_mode == "general"
    assert context.analysis_scope == "general"
    assert context.indicator_preference == "auto"
    assert context.confidence == "low"
    assert context.allowed_tool_names is None
    assert context.response_language == "english"
    assert context.should_clarify is False


def test_parse_intent_response_supports_new_taxonomy_intents():
    context = parse_intent_response(
        """
        {
          "intent": "alert_setup",
          "user_goal_type": "monitor",
          "goal_summary": "Set an alert for BTC breakout",
          "analysis_mode": "technical",
          "analysis_scope": "full_setup",
          "indicator_preference": "price_action_only",
          "need_indicator_confirmation": false,
          "inferred_indicator_hint": "breakout confirmation",
          "confidence": "high",
          "preferred_tool_groups": ["monitoring", "chart", "ui"],
          "routing_reason": "The user wants an actionable market alert",
          "response_language": "english",
          "should_clarify": false,
          "clarification_reason": "",
          "suggested_hint_title": "",
          "suggested_hint_options": []
        }
        """
    )

    assert context.intent == "alert_setup"
    assert context.user_goal_type == "monitor"
    assert "add_price_alert" in context.allowed_tool_names
    assert "tv_create_alert" in context.allowed_tool_names
    assert "show_hint" in context.allowed_tool_names
    assert "add_user_memory" not in context.allowed_tool_names


def test_parse_intent_response_supports_extended_design_intents_and_scopes():
    context = parse_intent_response(
        """
        {
          "intent": "portfolio_review",
          "user_goal_type": "scenario_planning",
          "goal_summary": "Review total crypto exposure and downside if BTC drops",
          "analysis_mode": "portfolio",
          "analysis_scope": "portfolio_review",
          "indicator_preference": "auto",
          "need_indicator_confirmation": false,
          "inferred_indicator_hint": "portfolio exposure and scenario stress",
          "confidence": "high",
          "preferred_tool_groups": ["market", "portfolio", "memory", "ui"],
          "routing_reason": "The user wants total portfolio health and downside analysis",
          "response_language": "english",
          "should_clarify": false,
          "clarification_reason": "",
          "suggested_hint_title": "",
          "suggested_hint_options": []
        }
        """
    )

    assert context.intent == "portfolio_review"
    assert context.user_goal_type == "scenario_planning"
    assert context.analysis_mode == "portfolio"
    assert context.analysis_scope == "portfolio_review"
    assert "get_price" in context.allowed_tool_names
    assert "backpack_get_collateral" in context.allowed_tool_names
    assert "get_user_memory" in context.allowed_tool_names
    assert "show_hint" in context.allowed_tool_names


def test_parse_intent_response_supports_combination_only_patterns():
    comparison_context = parse_intent_response(
        """
        {
          "intent": "market_analysis",
          "user_goal_type": "compare",
          "goal_summary": "Compare BTC and ETH setup quality today",
          "analysis_mode": "technical",
          "analysis_scope": "comparison",
          "indicator_preference": "indicator_light",
          "need_indicator_confirmation": false,
          "inferred_indicator_hint": "relative strength and market structure",
          "confidence": "high",
          "preferred_tool_groups": ["market", "chart", "ui"],
          "routing_reason": "The user wants a side-by-side market comparison",
          "response_language": "english",
          "should_clarify": false,
          "clarification_reason": "",
          "suggested_hint_title": "",
          "suggested_hint_options": []
        }
        """
    )
    education_context = parse_intent_response(
        """
        {
          "intent": "education",
          "user_goal_type": "learn_path",
          "goal_summary": "User wants to know what to learn next about options",
          "analysis_mode": "general",
          "analysis_scope": "general",
          "indicator_preference": "auto",
          "need_indicator_confirmation": false,
          "inferred_indicator_hint": "",
          "confidence": "high",
          "preferred_tool_groups": ["research", "ui"],
          "routing_reason": "The user is asking for a learning path rather than live market analysis",
          "response_language": "english",
          "should_clarify": false,
          "clarification_reason": "",
          "suggested_hint_title": "",
          "suggested_hint_options": []
        }
        """
    )

    assert comparison_context.intent == "market_analysis"
    assert comparison_context.user_goal_type == "compare"
    assert comparison_context.analysis_scope == "comparison"
    assert "get_price" in comparison_context.allowed_tool_names
    assert "tv_get_state" in comparison_context.allowed_tool_names

    assert education_context.intent == "education"
    assert education_context.user_goal_type == "learn_path"
    assert education_context.analysis_mode == "general"
    assert "web_search" in education_context.allowed_tool_names
    assert "show_hint" in education_context.allowed_tool_names


def test_news_impact_context_includes_dedicated_news_tools():
    context = parse_intent_response(
        """
        {
          "intent": "news_impact",
          "user_goal_type": "analyze",
          "goal_summary": "Assess whether recent BTC ETF headlines affect price reaction",
          "analysis_mode": "news",
          "analysis_scope": "full_setup",
          "indicator_preference": "auto",
          "need_indicator_confirmation": false,
          "inferred_indicator_hint": "",
          "confidence": "high",
          "preferred_tool_groups": ["research", "market", "ui"],
          "routing_reason": "The user wants news-driven market impact analysis",
          "response_language": "english",
          "should_clarify": false,
          "clarification_reason": "",
          "suggested_hint_title": "",
          "suggested_hint_options": []
        }
        """
    )

    assert context.intent == "news_impact"
    assert "get_latest_news" in context.allowed_tool_names
    assert "search_news_by_keywords" in context.allowed_tool_names
    assert "get_trending_news" in context.allowed_tool_names
    assert "search_news_by_symbols" in context.allowed_tool_names
    assert "web_search" in context.allowed_tool_names


def test_build_intent_prompt_documents_combination_only_patterns():
    prompt = build_intent_prompt(
        user_input="Is BTC or ETH better right now?",
        history=[],
        market_context={"scope_mode": "global"},
    )

    assert "comparison requests should usually map to intent=market_analysis" in prompt
    assert "second-opinion requests should usually map to market_analysis" in prompt
    assert "liquidity-check requests should usually map to market_analysis" in prompt
    assert 'knowledge-gap or "what should I learn next" requests should usually map to education' in prompt
    assert "combined information-retrieval surface that includes both general web search and dedicated news tools" in prompt
    assert "- portfolio" in prompt
    assert "- execution" in prompt


def test_tool_registry_can_filter_schema_by_allowed_names():
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="tool_a",
            description="A",
            parameters=[ToolParameter(name="query", type="string", description="q", required=True)],
            function=None,
        )
    )
    registry.register(
        ToolDefinition(
            name="tool_b",
            description="B",
            parameters=[],
            function=None,
        )
    )

    schema = registry.get_tools_schema(allowed_names={"tool_b"})

    assert [item["name"] for item in schema] == ["tool_b"]
